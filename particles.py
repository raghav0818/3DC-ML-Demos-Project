"""
particles.py — NumPy-vectorized particle system.

All particle state is stored in flat NumPy arrays so updates run as
vectorized C-level operations.  No Python loops in the hot path.

Two visual events use particles:
  1. Collision hits  → colored sparks burst from impact point
  2. High-score celebration → gold particles burst from center
"""

import numpy as np
import pygame

import config as cfg


class ParticleSystem:
    """
    Manages a pool of particles.  Pre-allocates arrays for the maximum
    count and tracks which slots are alive via a lifetime array.

    Usage:
        ps = ParticleSystem()
        ps.emit(x, y, count, color)        # spawn particles
        ps.update(dt)                       # physics step
        ps.render(surface)                  # draw
    """

    def __init__(self, max_count=None):
        self.max_count = max_count or cfg.PARTICLE_MAX_COUNT

        # Pre-allocate arrays (all particles, alive or dead)
        self.x = np.zeros(self.max_count, dtype=np.float32)
        self.y = np.zeros(self.max_count, dtype=np.float32)
        self.vx = np.zeros(self.max_count, dtype=np.float32)
        self.vy = np.zeros(self.max_count, dtype=np.float32)
        self.lifetime = np.zeros(self.max_count, dtype=np.float32)  # <= 0 = dead
        self.max_lifetime = np.zeros(self.max_count, dtype=np.float32)

        # Color per particle (R, G, B) — stored as separate arrays for speed
        self.r = np.zeros(self.max_count, dtype=np.uint8)
        self.g = np.zeros(self.max_count, dtype=np.uint8)
        self.b = np.zeros(self.max_count, dtype=np.uint8)

        # Size per particle
        self.size = np.ones(self.max_count, dtype=np.int32) * 2

        # Pointer to the next free slot (round-robin allocation)
        self._next_slot = 0

    def emit(self, x, y, count, color, speed_min=None, speed_max=None):
        """
        Spawn `count` particles at (x, y) with radial outward velocity
        in a random direction, colored with `color` (R, G, B tuple).
        """
        if count <= 0:
            return

        speed_min = speed_min or cfg.PARTICLE_SPEED_MIN
        speed_max = speed_max or cfg.PARTICLE_SPEED_MAX

        # Find slots to fill (overwrite dead or oldest particles)
        count = min(count, self.max_count)
        indices = np.arange(self._next_slot, self._next_slot + count) % self.max_count
        self._next_slot = (self._next_slot + count) % self.max_count

        n = len(indices)

        # Random angles and speeds for radial burst
        angles = np.random.uniform(0, 2 * np.pi, n).astype(np.float32)
        speeds = np.random.uniform(speed_min, speed_max, n).astype(np.float32)

        self.x[indices] = x
        self.y[indices] = y
        self.vx[indices] = np.cos(angles) * speeds
        self.vy[indices] = np.sin(angles) * speeds

        lifetimes = np.random.uniform(
            cfg.PARTICLE_LIFETIME * 0.5,
            cfg.PARTICLE_LIFETIME,
            n,
        ).astype(np.float32)
        self.lifetime[indices] = lifetimes
        self.max_lifetime[indices] = lifetimes

        self.r[indices] = color[0]
        self.g[indices] = color[1]
        self.b[indices] = color[2]

        self.size[indices] = np.random.randint(
            cfg.PARTICLE_SIZE_MIN, cfg.PARTICLE_SIZE_MAX + 1, n
        )

    def update(self, dt):
        """
        Physics step: move particles, apply drag, decay lifetime.
        All operations are vectorized — no Python loops.
        """
        # Find alive particles
        alive = self.lifetime > 0

        # Move
        self.x[alive] += self.vx[alive]
        self.y[alive] += self.vy[alive]

        # Drag (friction)
        self.vx[alive] *= cfg.PARTICLE_DRAG
        self.vy[alive] *= cfg.PARTICLE_DRAG

        # Slight gravity for a natural arc
        self.vy[alive] += 0.15

        # Decay lifetime
        self.lifetime[alive] -= dt

    def render(self, surface):
        """
        Draw all alive particles onto the PyGame surface.
        Uses pygame.draw.circle for each alive particle.
        This is the one place we have a Python loop, but it's bounded
        by the alive count (typically 200-500 at peak), not the total pool.
        """
        alive_mask = self.lifetime > 0
        indices = np.where(alive_mask)[0]

        if len(indices) == 0:
            return

        # Pre-compute alpha based on remaining lifetime fraction
        fracs = self.lifetime[indices] / np.maximum(self.max_lifetime[indices], 0.01)
        fracs = np.clip(fracs, 0, 1)

        # Batch extract values for the loop
        xs = self.x[indices].astype(int)
        ys = self.y[indices].astype(int)
        rs = self.r[indices]
        gs = self.g[indices]
        bs = self.b[indices]
        sizes = self.size[indices]

        sw, sh = surface.get_size()

        # Create an alpha surface for soft particles
        alpha_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        for i in range(len(indices)):
            px, py = int(xs[i]), int(ys[i])
            if 0 <= px < sw and 0 <= py < sh:
                alpha = int(fracs[i] * 255)
                color = (int(rs[i]), int(gs[i]), int(bs[i]), alpha)
                radius = max(1, int(sizes[i]))
                pygame.draw.circle(alpha_surf, color, (px, py), radius)

        surface.blit(alpha_surf, (0, 0))

    def clear(self):
        """Kill all particles."""
        self.lifetime[:] = 0

    @property
    def alive_count(self):
        """Number of currently alive particles (for debug display)."""
        return int(np.sum(self.lifetime > 0))
