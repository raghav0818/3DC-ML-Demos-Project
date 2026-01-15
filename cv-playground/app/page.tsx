'use client';

import { useState, useRef, useEffect } from 'react';
import Webcam from 'react-webcam';
import { useComputerVision } from '@/hooks/useComputerVision';
import { CVMode } from '@/types/cv';

export default function HomePage() {
    const [currentMode, setCurrentMode] = useState<CVMode>('clown-nose');
    const [isWebcamReady, setIsWebcamReady] = useState(false);

    const webcamRef = useRef<Webcam>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const videoElementRef = useRef<HTMLVideoElement | null>(null);

    const { isLoading, error, fps } = useComputerVision({
        mode: currentMode,
        videoElement: videoElementRef.current,
        canvasElement: canvasRef.current,
        enabled: isWebcamReady,
    });

    // Update video element ref when webcam is ready
    useEffect(() => {
        if (webcamRef.current && webcamRef.current.video) {
            videoElementRef.current = webcamRef.current.video;
        }
    }, [isWebcamReady]);

    const modes: { id: CVMode; label: string; icon: string; desc: string }[] = [
        { id: 'clown-nose', label: 'Clown Nose', icon: '🔴', desc: 'Face tracking filter' },
        { id: 'rock-paper', label: 'Rock Paper Scissors', icon: '✂️', desc: 'Hand gesture game' },
        { id: 'victory', label: 'Victory Pose', icon: '🎉', desc: 'Body pose detection' },
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
            {/* Header */}
            <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-700 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-white">
                                🎥 CV Playground
                            </h1>
                            <p className="text-slate-400 text-sm mt-1">
                                Real-time computer vision powered by MediaPipe
                            </p>
                        </div>
                        {!isLoading && !error && (
                            <div className="bg-neon-cyan/10 border border-neon-cyan/30 px-4 py-2 rounded-lg">
                                <p className="text-neon-cyan font-mono text-sm">
                                    {fps} FPS
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-6 py-8">
                {/* Mode Selector */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    {modes.map((mode) => (
                        <button
                            key={mode.id}
                            onClick={() => setCurrentMode(mode.id)}
                            className={`relative overflow-hidden rounded-2xl p-6 transition-all duration-300 ${currentMode === mode.id
                                ? 'bg-gradient-to-br from-neon-cyan/20 to-neon-cyan/10 border-2 border-neon-cyan shadow-lg shadow-neon-cyan/20 scale-105'
                                : 'bg-slate-800/50 border-2 border-slate-700 hover:border-slate-600 hover:bg-slate-800/70'
                                }`}
                        >
                            <div className="flex items-center gap-4">
                                <span className="text-5xl">{mode.icon}</span>
                                <div className="text-left">
                                    <h3 className="text-xl font-bold text-white">
                                        {mode.label}
                                    </h3>
                                    <p className="text-slate-400 text-sm mt-1">
                                        {mode.desc}
                                    </p>
                                </div>
                            </div>
                            {currentMode === mode.id && (
                                <div className="absolute inset-0 bg-gradient-to-r from-neon-cyan/0 via-neon-cyan/10 to-neon-cyan/0 animate-pulse-slow pointer-events-none" />
                            )}
                        </button>
                    ))}
                </div>

                {/* Video and Instructions Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    {/* Video Container - 3/4 width */}
                    <div className="lg:col-span-3">
                        <div className="relative aspect-video bg-slate-900 rounded-3xl overflow-hidden shadow-2xl border-2 border-slate-700">
                            {/* Webcam */}
                            <Webcam
                                ref={webcamRef}
                                audio={false}
                                screenshotFormat="image/jpeg"
                                videoConstraints={{
                                    width: 1280,
                                    height: 720,
                                    facingMode: 'user',
                                }}
                                onUserMedia={() => setIsWebcamReady(true)}
                                className="w-full h-full object-cover"
                                mirrored
                            />

                            {/* Canvas Overlay */}
                            <canvas
                                ref={canvasRef}
                                width={1280}
                                height={720}
                                className="absolute top-0 left-0 w-full h-full pointer-events-none"
                                style={{ transform: 'scaleX(-1)' }}
                            />

                            {/* Loading Overlay */}
                            {isLoading && (
                                <div className="absolute inset-0 bg-slate-900/95 backdrop-blur-sm flex flex-col items-center justify-center">
                                    <div className="relative">
                                        <div className="animate-spin rounded-full h-20 w-20 border-t-4 border-b-4 border-neon-cyan"></div>
                                        <div className="absolute inset-0 animate-ping rounded-full h-20 w-20 border-4 border-neon-cyan opacity-20"></div>
                                    </div>
                                    <p className="text-neon-cyan text-xl font-semibold mt-6 animate-pulse">
                                        Loading AI Models
                                    </p>
                                    <p className="text-slate-400 mt-2 text-sm">
                                        This may take a few moments...
                                    </p>
                                </div>
                            )}

                            {/* Error Overlay */}
                            {error && (
                                <div className="absolute inset-0 bg-red-900/90 backdrop-blur-sm flex flex-col items-center justify-center p-6">
                                    <div className="text-7xl mb-4">⚠️</div>
                                    <p className="text-white text-2xl font-bold mb-2">Oops! Something went wrong</p>
                                    <p className="text-red-200 text-center max-w-md">{error}</p>
                                    <button
                                        onClick={() => window.location.reload()}
                                        className="mt-6 bg-white text-red-900 px-6 py-3 rounded-lg font-semibold hover:bg-red-50 transition-colors"
                                    >
                                        Reload Page
                                    </button>
                                </div>
                            )}

                            {/* Mode Badge */}
                            {!isLoading && !error && (
                                <div className="absolute top-6 left-6 bg-slate-900/90 backdrop-blur-md px-5 py-3 rounded-xl border border-neon-cyan/30 shadow-lg">
                                    <div className="flex items-center gap-3">
                                        <span className="text-3xl">{modes.find(m => m.id === currentMode)?.icon}</span>
                                        <div>
                                            <p className="text-white font-bold text-sm">
                                                {modes.find(m => m.id === currentMode)?.label}
                                            </p>
                                            <p className="text-neon-cyan text-xs">
                                                Active
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Instructions Panel - 1/3 width on the right */}
                    {!isLoading && !error && (
                        <div className="lg:col-span-1">
                            <div className="sticky top-24 bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700 h-fit">
                                <div className="flex items-start gap-3">
                                    <span className="text-3xl">💡</span>
                                    <div className="flex-1">
                                        <h3 className="text-white font-bold text-lg mb-4">How to use</h3>

                                        {currentMode === 'clown-nose' && (
                                            <div className="space-y-3 text-slate-300">
                                                <p className="flex items-start gap-2">
                                                    <span className="text-neon-cyan mt-1">•</span>
                                                    <span>Position your face in front of the camera</span>
                                                </p>
                                                <p className="flex items-start gap-2">
                                                    <span className="text-neon-cyan mt-1">•</span>
                                                    <span>Watch the red circle appear on your nose</span>
                                                </p>
                                                <p className="flex items-start gap-2">
                                                    <span className="text-neon-cyan mt-1">•</span>
                                                    <span>Move closer or farther to see the circle resize</span>
                                                </p>
                                            </div>
                                        )}

                                        {currentMode === 'rock-paper' && (
                                            <div className="space-y-3 text-slate-300">
                                                <p className="flex items-start gap-2">
                                                    <span className="text-neon-cyan mt-1">•</span>
                                                    <span><strong className="text-red-400">Rock:</strong> Make a fist (0 fingers)</span>
                                                </p>
                                                <p className="flex items-start gap-2">
                                                    <span className="text-neon-cyan mt-1">•</span>
                                                    <span><strong className="text-blue-400">Scissors:</strong> Extend index + middle fingers only</span>
                                                </p>
                                                <p className="flex items-start gap-2">
                                                    <span className="text-neon-cyan mt-1">•</span>
                                                    <span><strong className="text-green-400">Paper:</strong> Open palm (all 5 fingers)</span>
                                                </p>
                                                <div className="mt-3 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                                                    <p className="text-blue-300 text-sm flex items-start gap-2">
                                                        <span>✂️</span>
                                                        <span>Tip: For scissors, keep ring + pinky fingers down!</span>
                                                    </p>
                                                </div>
                                            </div>
                                        )}

                                        {currentMode === 'victory' && (
                                            <div className="space-y-3 text-slate-300">
                                                <p className="flex items-start gap-2">
                                                    <span className="text-neon-cyan mt-1">•</span>
                                                    <span>Step back so your full body is visible</span>
                                                </p>
                                                <p className="flex items-start gap-2">
                                                    <span className="text-neon-cyan mt-1">•</span>
                                                    <span>Raise both hands above your head</span>
                                                </p>
                                                <p className="flex items-start gap-2">
                                                    <span className="text-neon-cyan mt-1">•</span>
                                                    <span>Watch for the golden "VICTORY!" celebration</span>
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </main>

            {/* Footer */}
            <footer className="mt-12 pb-6 text-center">
                <p className="text-slate-500 text-sm">
                    Built with Next.js, MediaPipe & WebGL • All processing happens in your browser
                </p>
            </footer>
        </div>
    );
}
