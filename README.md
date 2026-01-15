# 🎥 CV Playground

Real-time computer vision powered by MediaPipe - Experience face detection, hand gesture recognition, and body pose detection directly in your browser.

## ⚡ Quick Start

**Just downloaded from GitHub?** Run these commands:
```bash
# Navigate to the INNER folder (note the double folder name!)
cd Downloads\3DC-ML-Demos-Project-main\3DC-ML-Demos-Project-main

# Install dependencies (takes ~2-3 minutes)
npm run install-all

# Start the app
npm run dev
```
Then open [http://localhost:3000](http://localhost:3000) in your browser. 🚀

> **💡 Tip**: Use **Command Prompt (CMD)** on Windows, not PowerShell, to avoid script execution errors.


## 🚀 Features

- **🔴 Clown Nose Filter** - Real-time face tracking with dynamic nose overlay
- **✂️ Rock Paper Scissors** - Hand gesture recognition supporting Rock, Paper, and Scissors
- **🎉 Victory Pose** - Full body pose detection with celebration effects
- **⚡ Browser-Based** - All processing happens locally in your browser
- **📱 Responsive Design** - Works on desktop and mobile devices
- **🎨 Modern UI** - Beautiful dark theme with glassmorphism effects

## 🛠️ Technologies

- **[Next.js 15](https://nextjs.org/)** - React framework with App Router
- **[TypeScript](https://www.typescriptlang.org/)** - Type-safe development
- **[MediaPipe Tasks Vision](https://developers.google.com/mediapipe)** - AI/ML vision models
- **[TailwindCSS](https://tailwindcss.com/)** - Utility-first CSS framework
- **[react-webcam](https://github.com/mozmorris/react-webcam)** - Webcam component for React
- **WebGL** - GPU-accelerated rendering

## 📋 Prerequisites

Before running this project, ensure you have:

- **Node.js** 18 or higher ([Download](https://nodejs.org/))
- **npm** (comes with Node.js)
- A **modern web browser** (Chrome, Firefox, Edge, Safari)
- **Webcam access** enabled

## 🔧 Installation

### Option 1: Clone with Git
```bash
git clone https://github.com/raghav0818/3DC-ML-Demos-Project.git
cd 3DC-ML-Demos-Project
npm run install-all
npm run dev
```

### Option 2: Download ZIP from GitHub

> **⚠️ IMPORTANT**: When you download as ZIP from GitHub, the folder structure is nested!

1. **Download and extract** the ZIP file from GitHub
2. **Navigate to the correct directory**:
   ```bash
   cd Downloads\3DC-ML-Demos-Project-main\3DC-ML-Demos-Project-main
   ```
   ⚠️ Notice the **double nested folder** - this is how GitHub structures downloaded ZIPs!

3. **Install dependencies** (this will take a few minutes):
   ```bash
   npm run install-all
   ```

4. **Run the development server**:
   ```bash
   npm run dev
   ```

5. **Open your browser** and navigate to [http://localhost:3000](http://localhost:3000)

6. **Allow webcam access** when prompted by your browser

### Troubleshooting Installation

**Error: "Missing script: dev"**
- You're in the wrong directory! Make sure you're in the **inner** folder (the one that contains `package.json`)
- Check: run `dir` (Windows) or `ls` and verify you see `package.json` and `cv-playground` folder

**Error: "The system cannot find the path specified"**
- Dependencies not installed yet! Run `npm run install-all` first

**PowerShell script execution error**
- Use **Command Prompt (CMD)** instead of PowerShell
- Or run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in PowerShell first

## 📖 Usage

### Selecting a Mode

Click on one of the three mode cards at the top:
- **Clown Nose** - Face tracking filter
- **Rock Paper Scissors** - Hand gesture game
- **Victory Pose** - Body pose detection

### Face Detection Mode
1. Position your face in front of the camera
2. Watch the red clown nose appear and follow your movements
3. Move closer or farther to see the nose resize dynamically

### Hand Gesture Mode
- **Rock** 🪨: Make a closed fist (0 fingers extended)
- **Scissors** ✂️: Extend index and middle fingers only
- **Paper** 📄: Open palm with all 5 fingers extended

### Body Pose Mode
1. Step back so your full body is visible in the frame
2. Raise both hands above your head
3. Watch for the golden "VICTORY!" celebration

## 🎨 UI Features

- **Side Instructions Panel** - Context-aware instructions displayed alongside the video
- **Mode-Specific Colors** - Cyan (Face), Magenta (Hand), Gold (Pose)
- **Real-time FPS Counter** - Monitor performance
- **Responsive Grid Layout** - Optimized for different screen sizes
- **Sticky Instructions** - Instructions stay visible while scrolling

## 📁 Project Structure

```
cv-playground/
├── app/
│   ├── layout.tsx          # Root layout with metadata
│   ├── page.tsx            # Main application page
│   └── globals.css         # Global styles and Tailwind
├── hooks/
│   └── useComputerVision.ts # Custom hook for CV processing
├── types/
│   └── cv.ts               # TypeScript type definitions
├── public/                 # Static assets
├── tailwind.config.js      # Tailwind configuration
├── tsconfig.json           # TypeScript configuration
└── package.json            # Dependencies and scripts
```

## 🔌 API Reference

### useComputerVision Hook

Custom React hook that manages computer vision processing.

```typescript
const { isLoading, error, fps } = useComputerVision({
  mode: CVMode,           // 'clown-nose' | 'rock-paper' | 'victory'
  videoElement: HTMLVideoElement | null,
  canvasElement: HTMLCanvasElement | null,
  enabled: boolean
});
```

**Parameters:**
- `mode` - Current CV mode to run
- `videoElement` - Reference to video element
- `canvasElement` - Canvas for drawing overlays
- `enabled` - Whether processing is active

**Returns:**
- `isLoading` - Loading state for AI models
- `error` - Error message if any
- `fps` - Current frames per second

## 🧪 Development

### Available Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
```

### Adding a New CV Mode

1. Add the mode type to `types/cv.ts`
2. Implement detection logic in `useComputerVision.ts`
3. Update UI in `app/page.tsx`
4. Add instructions in the side panel

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Contribution Guidelines

- Follow the existing code style
- Write descriptive commit messages
- Add comments for complex logic
- Test your changes thoroughly
- Update documentation as needed

## 🐛 Troubleshooting

### Webcam Not Working
- Ensure webcam permissions are granted in browser settings
- Check that no other application is using the webcam
- Try a different browser

### Poor Performance
- Close other browser tabs
- Ensure good lighting conditions
- Use a modern browser with WebGL support
- Check FPS counter to monitor performance

### Models Not Loading
- Check your internet connection (models download on first run)
- Clear browser cache and reload
- Check browser console for error messages

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- **[MediaPipe](https://developers.google.com/mediapipe)** - For powerful ML models
- **[Next.js](https://nextjs.org/)** - For the amazing React framework
- **[Vercel](https://vercel.com/)** - For hosting and deployment
- **[TailwindCSS](https://tailwindcss.com/)** - For beautiful styling

## 📧 Contact

For questions, suggestions, or issues, please open an issue on GitHub.

---

**Built using Next.js, MediaPipe & WebGL**

*All processing happens in your browser - your privacy is protected!*
#
