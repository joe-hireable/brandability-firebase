export type SimilarityDegree = "identical" | "high_degree" | "medium_degree" | "low_degree" | "dissimilar";
export type ConceptualSimilarityDegree = "identical" | "high_degree" | "medium_degree" | "low_degree" | "dissimilar" | "neutral";

export interface MarkSimilarityRequest {
    applicant_mark: string;
    opponent_mark: string;
    mark_image_url?: string;
}

export interface MarkSimilarityOutput {
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

export interface GsSimilarityRequest {
    applicant_term: string;
    opponent_term: string;
    mark_similarity: MarkSimilarityOutput;
}

export interface GsSimilarityOutput {
    similarity: SimilarityDegree;
    similarity_score: number;
    is_competitive: boolean;
    is_complementary: boolean;
    likelihood_of_confusion: boolean;
    confusion_type?: "direct" | "indirect" | "both" | null;
    reasoning: string;
}