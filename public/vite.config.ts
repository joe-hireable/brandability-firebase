import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
import { resolve } from "path"
import tailwindcss from "@tailwindcss/vite"

export default defineConfig({
  root: './',
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      "@": resolve(__dirname, "./")
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5004/trademark-prediction-system/us-central1',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
