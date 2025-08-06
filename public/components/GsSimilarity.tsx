import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card";
import { Label } from "./ui/label";
import type { SimilarityDegree, ConceptualSimilarityDegree, ConfusionType } from "../lib/models";
import { Textarea } from "./ui/textarea";

interface MarkSimilarityOutput {
    visual: SimilarityDegree;
    aural: SimilarityDegree;
    conceptual: ConceptualSimilarityDegree;
    overall_similarity: SimilarityDegree;
    visual_score: number;
    aural_score: number;
    conceptual_score: number;
    overall_similarity_score: number;
    reasoning: string;
}

interface GsSimilarityResult {
    similarity: SimilarityDegree;
    similarity_score: number;
    is_competitive: boolean;
    is_complementary: boolean;
    likelihood_of_confusion: boolean;
    confusion_type: ConfusionType | null;
    reasoning: string;
}

export function GsSimilarity() {
    const [applicantTerm, setApplicantTerm] = useState("");
    const [opponentTerm, setOpponentTerm] = useState("");
    const [markSimilarity, setMarkSimilarity] = useState<MarkSimilarityOutput>({
        visual: "dissimilar",
        aural: "dissimilar",
        conceptual: "dissimilar",
        overall_similarity: "dissimilar",
        visual_score: 0,
        aural_score: 0,
        conceptual_score: 0,
        overall_similarity_score: 0,
        reasoning: "",
    });

    const [result, setResult] = useState<GsSimilarityResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleCalculate = async () => {
        if (!applicantTerm || !opponentTerm) {
            setError("Please fill in all fields.");
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch('/assess_gs_similarity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    applicant_term: applicantTerm,
                    opponent_term: opponentTerm,
                    mark_similarity: markSimilarity,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            setResult(data);

        } catch (err) {
            console.error("Error calling function:", err);
            setError("Failed to calculate similarity. See console for details.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="w-full">
            <CardHeader>
                <CardTitle>Goods & Services Similarity</CardTitle>
                <CardDescription>
                    Assess the similarity between two goods or services, providing context from the mark similarity assessment.
                </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
                <div className="grid md:grid-cols-2 gap-4">
                    <div className="grid gap-2">
                        <Label htmlFor="applicant-term">Applicant Term</Label>
                        <Input
                            id="applicant-term"
                            value={applicantTerm}
                            onChange={(e) => setApplicantTerm(e.target.value)}
                            placeholder="e.g., T-shirts"
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="opponent-term">Opponent Term</Label>
                        <Input
                            id="opponent-term"
                            value={opponentTerm}
                            onChange={(e) => setOpponentTerm(e.target.value)}
                            placeholder="e.g., Clothing"
                        />
                    </div>
                </div>
                <fieldset className="border p-4 rounded-md">
                    <legend className="text-sm font-medium px-1">Mark Similarity Context</legend>
                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
                        <div className="grid gap-2">
                            <Label htmlFor="overall_similarity_score">Overall Score</Label>
                            <Input
                                id="overall_similarity_score"
                                type="number"
                                value={markSimilarity.overall_similarity_score}
                                onChange={(e) => setMarkSimilarity({ ...markSimilarity, overall_similarity_score: parseFloat(e.target.value) })}
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="overall_similarity">Overall Degree</Label>
                            <Input
                                id="overall_similarity"
                                value={markSimilarity.overall_similarity}
                                onChange={(e) => setMarkSimilarity({ ...markSimilarity, overall_similarity: e.target.value as SimilarityDegree })}
                            />
                        </div>
                    </div>
                    <div className="grid gap-2 mt-4">
                        <Label htmlFor="mark-reasoning">Mark Similarity Reasoning</Label>
                        <Textarea
                            id="mark-reasoning"
                            value={markSimilarity.reasoning}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setMarkSimilarity({ ...markSimilarity, reasoning: e.target.value })}
                            placeholder="e.g., The marks are visually and aurally similar..."
                        />
                    </div>
                </fieldset>
            </CardContent>
            <CardFooter className="flex flex-col items-start">
                <Button onClick={handleCalculate} disabled={loading} className="w-full">
                    {loading ? "Calculating..." : "Calculate"}
                </Button>
                {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
                {result && (
                    <div className="mt-4 p-4 bg-gray-100 rounded-md w-full">
                        <h3 className="text-lg font-semibold">Result:</h3>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                            <p>Similarity Score:</p><p className="font-mono">{result.similarity_score.toFixed(2)}</p>
                            <p>Similarity Degree:</p><p className="font-mono">{result.similarity}</p>
                            <p>Competitive:</p><p className="font-mono">{result.is_competitive ? "Yes" : "No"}</p>
                            <p>Complementary:</p><p className="font-mono">{result.is_complementary ? "Yes" : "No"}</p>
                            <p>Likelihood of Confusion:</p><p className="font-mono">{result.likelihood_of_confusion ? "Yes" : "No"}</p>
                            {result.confusion_type && <><p>Confusion Type:</p><p className="font-mono">{result.confusion_type}</p></>}
                        </div>
                        <p className="mt-4">
                            <span className="font-semibold">Reasoning:</span> {result.reasoning}
                        </p>
                    </div>
                )}
            </CardFooter>
        </Card>
    );
}