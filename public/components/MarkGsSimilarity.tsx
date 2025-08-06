import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card";
import { Label } from "./ui/label";
import type { SimilarityDegree } from "../lib/models";

interface GsSimilarityResult {
    similarity_score: number;
    similarity: SimilarityDegree;
    reasoning: string;
}

export function MarkGsSimilarity() {
    const [applicantTerm, setApplicantTerm] = useState("");
    const [applicantClass, setApplicantClass] = useState("");
    const [opponentTerm, setOpponentTerm] = useState("");
    const [opponentClass, setOpponentClass] = useState("");
    const [result, setResult] = useState<GsSimilarityResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleCalculate = async () => {
        if (!applicantTerm || !opponentTerm || !applicantClass || !opponentClass) {
            setError("Please fill in all fields.");
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch('/calculate_gs_similarity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    applicant_term: {
                        term: applicantTerm,
                        class: parseInt(applicantClass, 10),
                    },
                    opponent_term: {
                        term: opponentTerm,
                        class: parseInt(opponentClass, 10),
                    },
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
        <Card className="w-full max-w-md">
            <CardHeader>
                <CardTitle>Goods & Services Similarity</CardTitle>
                <CardDescription>
                    Enter two Goods or Services to calculate their conceptual similarity using a Large Language Model with RAG.
                </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
                <div className="grid grid-cols-3 gap-2">
                    <div className="col-span-2 grid gap-2">
                        <Label htmlFor="applicant-term-gs">Applicant Term</Label>
                        <Input
                            id="applicant-term-gs"
                            value={applicantTerm}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setApplicantTerm(e.target.value)}
                            placeholder="e.g., Coffee"
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="applicant-class-gs">Class</Label>
                        <Input
                            id="applicant-class-gs"
                            type="number"
                            value={applicantClass}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setApplicantClass(e.target.value)}
                            placeholder="e.g., 30"
                        />
                    </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                     <div className="col-span-2 grid gap-2">
                        <Label htmlFor="opponent-term-gs">Opponent Term</Label>
                        <Input
                            id="opponent-term-gs"
                            value={opponentTerm}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOpponentTerm(e.target.value)}
                            placeholder="e.g., Tea"
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="opponent-class-gs">Class</Label>
                        <Input
                            id="opponent-class-gs"
                            type="number"
                            value={opponentClass}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOpponentClass(e.target.value)}
                            placeholder="e.g., 30"
                        />
                    </div>
                </div>
            </CardContent>
            <CardFooter className="flex flex-col items-start">
                <Button onClick={handleCalculate} disabled={loading} className="w-full">
                    {loading ? "Calculating..." : "Calculate"}
                </Button>
                {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
                {result && (
                    <div className="mt-4 p-4 bg-gray-100 rounded-md w-full">
                        <h3 className="text-lg font-semibold">Result:</h3>
                        <p>
                            Similarity Score:{" "}
                            <span className="font-mono">
                                {result.similarity_score.toFixed(2)}
                            </span>
                        </p>
                        <p>
                            Similarity Degree:{" "}
                            <span className="font-mono">{result.similarity}</span>
                        </p>
                        <p className="mt-2">
                            <span className="font-semibold">Reasoning:</span> {result.reasoning}
                        </p>
                    </div>
                )}
            </CardFooter>
        </Card>
    );
}