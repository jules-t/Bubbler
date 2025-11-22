import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { BubbleVisualization } from "@/components/BubbleVisualization";
import { CATEGORIES, Category } from "@/types/bubble";
import { Card } from "@/components/ui/card";

const Index = () => {
  const navigate = useNavigate();
  const [categories] = useState<Category[]>(CATEGORIES);
  const [marketScore, setMarketScore] = useState(0);
  const [userScore, setUserScore] = useState(0);

  const calculateScore = (cats: Category[], useUserWeights: boolean = false) => {
    if (useUserWeights) {
      // User score calculation - matches UserAnalysis.tsx
      let totalScore = 0;
      
      cats.forEach(category => {
        const categoryScore = category.indexes.reduce((sum, index) => {
          const indexValue = index.userValue !== undefined ? index.userValue : index.value;
          return sum + indexValue;
        }, 0) / category.indexes.length;
        
        totalScore += categoryScore * (category.userWeight / 100);
      });
      
      return Math.min(100, totalScore / cats.length);
    } else {
      // Market score calculation
      let totalScore = 0;
      let totalWeight = 0;

      cats.forEach((category) => {
        const categoryScore =
          category.indexes.reduce((sum, index) => sum + index.value, 0) / category.indexes.length;

        totalScore += categoryScore * category.marketWeight;
        totalWeight += category.marketWeight;
      });

      return totalWeight > 0 ? Math.min(100, totalScore / totalWeight) : 0;
    }
  };

  useEffect(() => {
    // Calculate market score
    setMarketScore(calculateScore(categories, false));

    // Load user categories from localStorage
    const savedUserCategories = localStorage.getItem("userCategories");
    if (savedUserCategories) {
      try {
        const parsed = JSON.parse(savedUserCategories);
        setUserScore(calculateScore(parsed, true));
      } catch (e) {
        setUserScore(calculateScore(categories, true));
      }
    } else {
      setUserScore(calculateScore(categories, true));
    }
  }, [categories]);

  return (
    <div className="min-h-screen bg-background dark">
      {/* Hero Section */}
      <div className="relative overflow-hidden border-b border-border bg-gradient-to-b from-background to-card">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/5" />
        <div className="relative container mx-auto px-4 py-16">
          <div className="text-center space-y-4">
            <h1 className="text-5xl font-bold text-primary">AI Bubble Visualizer</h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Analyze the AI market bubble using key economic indicators. Click on each bubble to explore detailed
              analysis.
            </p>
          </div>
        </div>
      </div>

      {/* Main Content - Two Bubbles */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Market Consensus Bubble */}
          <Card
            className="p-8 bg-card border-border cursor-pointer hover:border-primary/50 transition-colors"
            onClick={() => navigate("/market-consensus")}
          >
            <BubbleVisualization
              score={marketScore}
              title="Market Consensus"
              subtitle="Algorithm reflecting real-time market factors"
            />
          </Card>

          {/* User Analysis Bubble */}
          <Card
            className="p-8 bg-card border-border cursor-pointer hover:border-primary/50 transition-colors"
            onClick={() => navigate("/user-analysis")}
          >
            <BubbleVisualization
              score={userScore}
              title="Your Analysis"
              subtitle="Assign your own weights in factors in estimating AI bubble"
            />
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Index;
