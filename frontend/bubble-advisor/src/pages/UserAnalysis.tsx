import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { BubbleVisualization } from "@/components/BubbleVisualization";
import { BubbleTrendChart } from "@/components/BubbleTrendChart";
import { CategoryControls } from "@/components/CategoryControls";
import { CATEGORIES, Category } from "@/types/bubble";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { useVoiceAgent } from "@/hooks/useVoiceAgent";
import { useBubbleState, useInitializeBubbleFromCategories } from "@/hooks/useBubbleState";
import { useToast } from "@/hooks/use-toast";

const UserAnalysis = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [categories, setCategories] = useState<Category[]>(CATEGORIES);
  const [userScore, setUserScore] = useState(0);

  const BUBBLE_ID = "personal_user";
  const { data: bubbleState, isLoading, error } = useBubbleState(BUBBLE_ID);
  const { initializeFromCategories, isPending: isInitializing } = useInitializeBubbleFromCategories();
  const { isListening, isProcessing, startRecording, stopRecording } = useVoiceAgent(BUBBLE_ID);

  const calculateScore = (cats: Category[]) => {
    let totalScore = 0;

    cats.forEach(category => {
      const categoryScore = category.indexes.reduce((sum, index) => {
        const indexValue = index.userValue !== undefined ? index.userValue : index.value;
        return sum + indexValue;
      }, 0) / category.indexes.length;

      totalScore += categoryScore * (category.userWeight / 100);
    });

    return Math.min(100, totalScore / cats.length);
  };

  useEffect(() => {
    const clientScore = calculateScore(categories);
    setUserScore(clientScore);
    // Autosave to localStorage
    localStorage.setItem('userCategories', JSON.stringify(categories));

    // Update backend bubble state when categories change
    initializeFromCategories(BUBBLE_ID, categories, true); // true = use user values
  }, [categories]);

  // Load from localStorage on mount
  useEffect(() => {
    const savedCategories = localStorage.getItem('userCategories');
    if (savedCategories) {
      try {
        const parsed = JSON.parse(savedCategories);
        setCategories(parsed);
      } catch (e) {
        console.error('Failed to load saved categories');
      }
    }
  }, []);

  // Use backend score if available, otherwise use client-calculated score
  const displayScore = bubbleState?.risk_score ?? userScore;

  // Show error toast if backend fails
  useEffect(() => {
    if (error) {
      toast({
        title: "Backend Connection Error",
        description: "Using local calculation. Make sure backend is running.",
        variant: "destructive",
      });
    }
  }, [error, toast]);

  const handleCategoryWeightChange = (categoryId: string, weight: number) => {
    setCategories((prev) =>
      prev.map((cat) =>
        cat.id === categoryId ? { ...cat, userWeight: weight } : cat
      )
    );
  };

  const handleIndexValueChange = (categoryId: string, indexId: string, value: number) => {
    setCategories((prev) =>
      prev.map((cat) => {
        if (cat.id === categoryId) {
          return {
            ...cat,
            indexes: cat.indexes.map(idx =>
              idx.id === indexId ? { ...idx, userValue: value } : idx
            ),
          };
        }
        return cat;
      })
    );
  };

  const handleReset = () => {
    setCategories(
      CATEGORIES.map((cat) => ({
        ...cat,
        userWeight: cat.marketWeight,
        indexes: cat.indexes.map(idx => ({ ...idx, userValue: undefined }))
      }))
    );
  };

  return (
    <div className="min-h-screen bg-background dark">
      {/* Header */}
      <div className="relative overflow-hidden border-b border-border bg-gradient-to-b from-background to-card">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/5" />
        <div className="relative container mx-auto px-4 py-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="mb-4 text-white hover:text-white/80"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Overview
          </Button>
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold text-primary">
              Your Analysis
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Customize factor weights to create your own bubble analysis
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-12">
        {/* Bubble Visualization */}
        <div className="mb-12">
          <Card className="p-8 bg-card border-border">
            <div className="mb-4 text-center">
              <div className="text-sm text-muted-foreground">
                Market Consensus: <span className="font-semibold text-primary">{(() => {
                  // Calculate market consensus score using market weights and values
                  let totalScore = 0;
                  const marketCategories = CATEGORIES.map(cat => ({
                    ...cat,
                    indexes: cat.indexes.map(idx => ({ ...idx, userValue: undefined }))
                  }));
                  
                  marketCategories.forEach(category => {
                    const categoryScore = category.indexes.reduce((sum, index) => sum + index.value, 0) / category.indexes.length;
                    totalScore += categoryScore * (category.marketWeight / 100);
                  });
                  
                  return Math.min(100, totalScore / marketCategories.length).toFixed(1);
                })()}</span>
              </div>
            </div>
            <BubbleVisualization
              score={displayScore}
              title="Your Analysis"
              subtitle={bubbleState ? `Risk Level: ${bubbleState.risk_level}` : "Custom factor weights"}
              isUserBubble
              onVoiceStart={startRecording}
              onVoiceStop={stopRecording}
              isListening={isListening}
            />
            {bubbleState?.personality && (
              <div className="mt-4 p-4 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">
                  <strong>Bubble Personality:</strong> {bubbleState.personality}
                </p>
              </div>
            )}
          </Card>
        </div>

        {/* Trend Chart */}
        <div className="mb-12">
          <BubbleTrendChart currentScore={userScore} />
        </div>

        {/* User Controls - Fully Editable */}
        <div>
          <CategoryControls
            categories={categories}
            onCategoryWeightChange={handleCategoryWeightChange}
            onIndexValueChange={handleIndexValueChange}
            onReset={handleReset}
          />
        </div>
      </div>
    </div>
  );
};

export default UserAnalysis;
