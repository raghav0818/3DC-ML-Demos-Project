# 🎥 CV Playground

Real-time computer vision powered by MediaPipe - Experience face detection, hand gesture recognition, and body pose detection directly in your browser.

![CV Playground Demo](https://img.shields.io/badge/MediaPipe-Powered-00D4FF?style=for-the-badge&logo=google&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)

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

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd "3DC Open House ML Project/cv-playground"
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run the development server**
   ```bash
   npm run dev
   ```

4. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

5. **Allow webcam access** when prompted by your browser

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

**Built with ❤️ using Next.js, MediaPipe & WebGL**

*All processing happens in your browser - your privacy is protected!*
#   3 D C - M L - D e m o s - P r o j e c t  
 