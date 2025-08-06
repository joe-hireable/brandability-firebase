import { FileUpload } from "./components/FileUpload";
import { MarkAuralSimilarity } from "./components/MarkAuralSimilarity";
import { MarkConceptualSimilarity } from "./components/MarkConceptualSimilarity";
import { MarkVisualSimilarity } from "./components/MarkVisualSimilarity";

function App() {
  return (
    <div className="container mx-auto p-4">
      <header className="text-center mb-12">
        <h1 className="text-4xl font-bold tracking-tight">Brandability</h1>
        <p className="text-xl text-muted-foreground mt-2">
          AI-powered trademark analysis.
        </p>
      </header>

      <div className="mb-12">
        <h2 className="text-2xl font-semibold mb-4">Case Analysis</h2>
        <p className="mb-4 text-muted-foreground">
          Upload your case documents to automatically extract key information and
          predict potential outcomes.
        </p>
        <FileUpload />
      </div>

      <div>
        <h2 className="text-2xl font-semibold mb-4 border-t pt-8">
          Similarity Tools
        </h2>
        <p className="mb-8 text-muted-foreground">
          Use the tools below to assess similarity between trademarks on
          different vectors.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <MarkVisualSimilarity />
          <MarkAuralSimilarity />
          <MarkConceptualSimilarity />
        </div>
      </div>
    </div>
  )
}

export default App
