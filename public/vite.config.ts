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
      '/calculate_visual_similarity': {
        target: 'http://localhost:5004/trademark-prediction-system/europe-west2',
        changeOrigin: true,
      },
      '/calculate_aural_similarity': {
        target: 'http://localhost:5004/trademark-prediction-system/europe-west2',
        changeOrigin: true,
      },
      '/calculate_conceptual_similarity': {
        target: 'http://localhost:5004/trademark-prediction-system/europe-west2',
        changeOrigin: true,
      },
      '/calculate_gs_similarity': {
        target: 'http://localhost:5004/trademark-prediction-system/europe-west2',
        changeOrigin: true,
      }
    }
  }
})
