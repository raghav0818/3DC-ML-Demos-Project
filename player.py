"""
player.py — Player body rendering (neon silhouette pipeline).

Transforms the raw binary body mask from MediaPipe into the glowing
neon outline that appears on screen.  The pipeline is:

  1. Gaussian blur on mask to smooth edges
  2. Canny edge detection to extract contour
  3. Dilate to thicken the contour
  4. Colorize the contour in electric cyan
  5. Gaussian blur on the colored contour to create glow halo
  6. Composite sharp contour on top of blurred glow

The result mimics actual neon tube lighting — a sharp bright core
surrounded by a soft luminous halo.
"""

import math
import cv2
import numpy as np
import pygame

import config as cfg


class PlayerRenderer:
    """
    Takes a binary body mask and produces a PyGame surface with the
    neon silhouette effect.  Also handles invincibility flash animation.
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Pre-build the dilation kernel so we don't recreate it per frame
        k = cfg.BODY_DILATE_KERNEL
        self._dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))

        # Neon color in BGR (for OpenCV operations) and RGB (for PyGame)
        self._neon_bgr = np.array(cfg.COLOR_BODY_NEON[::-1], dtype=np.uint8)
        self._neon_rgb = cfg.COLOR_BODY_NEON

    def render_body(self, body_mask, is_invincible=False, time_now=0.0):
        """
        Given a binary body mask (uint8, 0 or 255), return a PyGame
        Surface (SRCALPHA) with the neon silhouette rendered on it.

        If is_invincible is True, the silhouette flashes on/off at
        INVINCIBILITY_FLASH_HZ frequency.
        """
        # During invincibility, flash the body outline
        if is_invincible:
            flash = math.sin(time_now * cfg.INVINCIBILITY_FLASH_HZ * 2 * math.pi)
            if flash < 0:
                # Return an empty surface (body is "invisible" this frame)
                return pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # ── Step 1: Smooth the mask ──
        # Gaussian blur reduces jagged edges from the segmentation output
        blurred_mask = cv2.GaussianBlur(
            body_mask,
            (cfg.BODY_BLUR_KERNEL, cfg.BODY_BLUR_KERNEL),
            0,
        )

        # ── Step 2: Edge detection ──
        edges = cv2.Canny(blurred_mask, cfg.BODY_CANNY_LOW, cfg.BODY_CANNY_HIGH)

        # ── Step 3: Thicken the edges ──
        thick_edges = cv2.dilate(
            edges,
            self._dilate_kernel,
            iterations=cfg.BODY_DILATE_ITERATIONS,
        )

        # ── Step 4: Colorize the edges ──
        # Create a 3-channel BGR image where edge pixels are the neon color
        colored_edges = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        colored_edges[thick_edges > 0] = self._neon_bgr

        # ── Step 5: Create the glow halo ──
        # Blur the colored edges to create a soft luminous spread
        glow = cv2.GaussianBlur(
            colored_edges,
            (cfg.BODY_GLOW_KERNEL, cfg.BODY_GLOW_KERNEL),
            0,
        )

        # ── Step 6: Composite sharp edges on top of glow ──
        # The glow is the base layer, the sharp edges sit on top
        composite = cv2.addWeighted(
            glow, cfg.BODY_GLOW_INTENSITY,
            colored_edges, 1.0,
            0,
        )

        # Also add a faint filled silhouette for additional visual presence
        # (very low opacity so the neon outline is still the star)
        filled = np.zeros_like(composite)
        filled[body_mask > 0] = self._neon_bgr
        composite = cv2.addWeighted(composite, 1.0, filled, 0.08, 0)

        # ── Convert to PyGame surface ──
        # OpenCV is BGR, PyGame expects RGB
        rgb = cv2.cvtColor(composite, cv2.COLOR_BGR2RGB)

        # Create an alpha channel: pixels with any color get full alpha,
        # pure black pixels get 0 alpha (transparent)
        gray = cv2.cvtColor(composite, cv2.COLOR_BGR2GRAY)
        alpha = np.where(gray > 5, 255, 0).astype(np.uint8)

        # Stack into RGBA
        rgba = np.dstack((rgb, alpha))

        # Create PyGame surface from the numpy array
        surface = pygame.image.frombuffer(
            rgba.tobytes(), (self.width, self.height), "RGBA"
        )

        return surface

    def render_body_simple(self, body_mask, is_invincible=False, time_now=0.0):
        """
        Simplified body rendering (no edge detection, just filled
        silhouette with glow).  Used as a performance fallback if
        the full pipeline is too slow.
        """
        if is_invincible:
            flash = math.sin(time_now * cfg.INVINCIBILITY_FLASH_HZ * 2 * math.pi)
            if flash < 0:
                return pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Simple: just colorize the mask directly with some blur for glow
        colored = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        colored[body_mask > 0] = self._neon_bgr

        glow = cv2.GaussianBlur(colored, (15, 15), 0)
        composite = cv2.addWeighted(glow, 0.5, colored, 1.0, 0)

        rgb = cv2.cvtColor(composite, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(composite, cv2.COLOR_BGR2GRAY)
        alpha = np.where(gray > 5, 255, 0).astype(np.uint8)
        rgba = np.dstack((rgb, alpha))

        surface = pygame.image.frombuffer(
            rgba.tobytes(), (self.width, self.height), "RGBA"
        )
        return surface
