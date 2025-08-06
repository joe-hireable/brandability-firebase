import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card";
import { Label } from "./ui/label";
import type { SimilarityDegree } from "../lib/models";

interface VisualSimilarityResult {
    score: number;
    degree: SimilarityDegree;
}

export function MarkVisualSimilarity() {
    const [applicantMark, setApplicantMark] = useState("");
    const [opponentMark, setOpponentMark] = useState("");
    const [result, setResult] = useState<VisualSimilarityResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleCalculate = async () => {
        if (!applicantMark || !opponentMark) {
            setError("Please fill in both marks.");
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            // Use the new API endpoint
            const response = await fetch('/api/calculateVisualSimilarity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    applicant_mark: applicantMark,
                    opponent_mark: opponentMark,
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
                <CardTitle>Visual Similarity</CardTitle>
                <CardDescription>
                    Enter two wordmarks to calculate their visual similarity based on the
                    Levenshtein distance.
                </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
                <div className="grid gap-2">
                    <Label htmlFor="applicant-mark">Applicant Mark</Label>
                    <Input
                        id="applicant-mark"
                        value={applicantMark}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setApplicantMark(e.target.value)}
                        placeholder="e.g., Coca-Cola"
                    />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="opponent-mark">Opponent Mark</Label>
                        <Input
                            id="opponent-mark"
                            value={opponentMark}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOpponentMark(e.target.value)}
                            placeholder="e.g., Koka-Kola"
                        />
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
                                {result.score.toFixed(2)}
                            </span>
                        </p>
                        <p>
                            Similarity Degree:{" "}
                            <span className="font-mono">{result.degree}</span>
                        </p>
                    </div>
                )}
            </CardFooter>
        </Card>
    );
}