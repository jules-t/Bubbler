import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { BubbleVisualization } from "@/components/BubbleVisualization";

import { MarketFactorsReadOnly } from "@/components/MarketFactorsReadOnly";
import { CATEGORIES, Category } from "@/types/bubble";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { useVoiceAgent } from "@/hooks/useVoiceAgent";

const MarketConsensus = () => {
  const navigate = useNavigate();
  const [categories] = useState<Category[]>(CATEGORIES);
  const [marketScore, setMarketScore] = useState(0);
  const { isListening, isProcessing, startRecording, stopRecording } = useVoiceAgent();

  const calculateScore = (cats: Category[]) => {
    let totalScore = 0;
    let totalWeight = 0;
    
    cats.forEach(category => {
      const categoryScore = category.indexes.reduce((sum, index) => {
        return sum + index.value;
      }, 0) / category.indexes.length;
      
      totalScore += categoryScore * category.marketWeight;
      totalWeight += category.marketWeight;
    });
    
    return totalWeight > 0 ? Math.min(100, totalScore / totalWeight) : 0;
  };

  useEffect(() => {
    setMarketScore(calculateScore(categories));
  }, [categories]);

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
              Market Consensus
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              View current market bubble analysis based on consensus data
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-12">
        {/* Bubble Visualization */}
        <div className="mb-12">
          <Card className="p-8 bg-card border-border">
            <BubbleVisualization
              score={marketScore}
              title="Market Consensus"
              subtitle="Based on current market data"
              isUserBubble
              onVoiceStart={startRecording}
              onVoiceStop={stopRecording}
              isListening={isListening}
            />
          </Card>
        </div>


        {/* Market Factors - Read Only with Educational Content */}
        <div>
          <MarketFactorsReadOnly categories={categories} />
        </div>
      </div>
    </div>
  );
};

export default MarketConsensus;
