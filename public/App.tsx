import { useState } from "react"
import { Button } from "./components/ui/button"
import DesignSystem from "./DesignSystem"

function App() {
  const [showDesignSystem, setShowDesignSystem] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-serif font-bold text-brand-primary">Brandability</h1>
          <Button
            variant={showDesignSystem ? "secondary" : "default"}
            onClick={() => setShowDesignSystem(!showDesignSystem)}
          >
            {showDesignSystem ? "View App" : "View Design System"}
          </Button>
        </div>
      </header>

      <main className="container mx-auto py-8">
        {showDesignSystem ? (
          <DesignSystem />
        ) : (
          <div className="max-w-3xl mx-auto text-center py-12">
            <h1 className="text-4xl font-serif font-bold text-brand-primary mb-6">
              Welcome to Brandability
            </h1>
            <p className="text-lg text-brand-text-secondary mb-8">
              The complete platform for trademark lawyers to assess, strategize, and
              prepare for trademark cases more efficiently.
            </p>
            <div className="flex gap-4 justify-center">
              <Button size="lg">Get Started</Button>
              <Button variant="outline" size="lg">Learn More</Button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
