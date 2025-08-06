import { FileUpload } from "./components/FileUpload";
import { MarkVisualSimilarity } from "./components/MarkVisualSimilarity";

function App() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Welcome to Brandability</h1>
      <p className="mb-8">
        Upload your case documents below to begin the analysis.
      </p>
      <FileUpload />
      <div className="mt-8">
        <MarkVisualSimilarity />
      </div>
    </div>
  )
}

export default App
