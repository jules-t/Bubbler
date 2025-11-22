import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, RotateCcw, Info, FileText } from "lucide-react";
import { Category, Index } from "@/types/bubble";
import { motion, AnimatePresence } from "framer-motion";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface CategoryControlsProps {
  categories: Category[];
  onCategoryWeightChange: (categoryId: string, weight: number) => void;
  onCategoryScoreChange?: (categoryId: string, score: number) => void;
  onIndexValueChange?: (categoryId: string, indexId: string, value: number) => void;
  onReset: () => void;
  readOnly?: boolean;
}

export const CategoryControls = ({
  categories,
  onCategoryWeightChange,
  onCategoryScoreChange,
  onIndexValueChange,
  onReset,
  readOnly = false,
}: CategoryControlsProps) => {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showExplanations, setShowExplanations] = useState<Set<string>>(new Set());
  const [showCategoryExplanations, setShowCategoryExplanations] = useState<Set<string>>(new Set());

  const toggleCategory = (categoryId: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId);
    } else {
      newExpanded.add(categoryId);
    }
    setExpandedCategories(newExpanded);
  };

  const toggleExplanation = (categoryId: string) => {
    const newExplanations = new Set(showExplanations);
    if (newExplanations.has(categoryId)) {
      newExplanations.delete(categoryId);
    } else {
      newExplanations.add(categoryId);
    }
    setShowExplanations(newExplanations);
  };

  const toggleCategoryExplanation = (categoryId: string) => {
    const newExplanations = new Set(showCategoryExplanations);
    if (newExplanations.has(categoryId)) {
      newExplanations.delete(categoryId);
    } else {
      newExplanations.add(categoryId);
    }
    setShowCategoryExplanations(newExplanations);
  };

  const getCategoryScore = (category: Category, useUserValues: boolean = false) => {
    return category.indexes.reduce((sum, index) => {
      const value = useUserValues && index.userValue !== undefined ? index.userValue : index.value;
      return sum + value;
    }, 0) / category.indexes.length;
  };

  const getMarketCategoryScore = (category: Category) => {
    return category.indexes.reduce((sum, index) => {
      return sum + index.value;
    }, 0) / category.indexes.length;
  };

  const getContribution = (category: Category) => {
    const categoryScore = getCategoryScore(category, true);
    return (categoryScore * category.userWeight) / 100;
  };

  const getTotalScore = () => {
    let totalScore = 0;
    categories.forEach(cat => {
      const categoryScore = getCategoryScore(cat, true);
      totalScore += categoryScore * (cat.userWeight / 100);
    });
    return Math.min(100, totalScore / categories.length);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-primary">Market Factors</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Adjust weights and values to customize your analysis
          </p>
        </div>
        {!readOnly && (
          <Button
            variant="outline"
            size="sm"
            onClick={onReset}
            className="gap-2"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </Button>
        )}
      </div>

      {!readOnly && (
        <div className="flex gap-2">
          <Button
            variant={!showAdvanced ? "default" : "outline"}
            onClick={() => setShowAdvanced(false)}
            className="flex-1"
          >
            Normal Controls
          </Button>
          <Button
            variant={showAdvanced ? "default" : "outline"}
            onClick={() => setShowAdvanced(true)}
            className="flex-1"
          >
            Advanced Controls
          </Button>
        </div>
      )}

      <div className="space-y-4">
        {categories.map((category) => {
          const isExpanded = expandedCategories.has(category.id);
          const showExplanation = showExplanations.has(category.id);
          const showCategoryExplanation = showCategoryExplanations.has(category.id);
          const contribution = getContribution(category);
          const totalScore = getTotalScore();
          const contributionPercentage = totalScore > 0 ? (contribution / totalScore) * 100 : 0;

          return (
            <Card
              key={category.id}
              className="p-6 bg-card border-border hover:border-primary/30 transition-all duration-200"
            >
              <div>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold text-foreground">
                        {category.name}
                      </h3>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleCategoryExplanation(category.id);
                        }}
                      >
                        <Info className="w-4 h-4 text-muted-foreground" />
                      </Button>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {category.description}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-primary">
                      {category.userWeight.toFixed(0)}%
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Market: {getMarketCategoryScore(category).toFixed(0)}
                    </div>
                  </div>
                  {showAdvanced && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="ml-2"
                      onClick={() => toggleCategory(category.id)}
                    >
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </Button>
                  )}
                </div>

                {/* Category Explanation */}
                <AnimatePresence>
                  {showCategoryExplanation && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden mb-4"
                    >
                      <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                        <p className="text-sm text-foreground leading-relaxed">
                          {category.explanation}
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Normal Mode: Category Slider */}
                {!showAdvanced && (
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-muted-foreground">
                          Category Score: {
                            (category.userCategoryScore ?? getCategoryScore(category, true)).toFixed(0)
                          }
                        </span>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                              <Info className="w-3 h-3 text-muted-foreground" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Adjust the overall score for this category (0-100)</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                      <div className="relative">
                        <Slider
                          value={[category.userCategoryScore ?? getCategoryScore(category, true)]}
                          onValueChange={([value]) => {
                            if (onCategoryScoreChange) {
                              onCategoryScoreChange(category.id, value);
                            }
                          }}
                          min={0}
                          max={100}
                          step={1}
                          className="mb-2"
                          disabled={readOnly}
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>0</span>
                          <span>100</span>
                        </div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-muted-foreground">
                          Weight: {category.userWeight}%
                        </span>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                              <Info className="w-3 h-3 text-muted-foreground" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Adjust category importance (0% = Ignore, 100% = Maximum)</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                      <div className="relative">
                        <Slider
                          value={[category.userWeight]}
                          onValueChange={([value]) =>
                            onCategoryWeightChange(category.id, value)
                          }
                          min={0}
                          max={100}
                          step={1}
                          className="mb-2"
                          disabled={readOnly}
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>0</span>
                          <span>100</span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-muted-foreground">Contribution to Total</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleExplanation(category.id);
                            }}
                          >
                            <FileText className="w-3 h-3" />
                          </Button>
                        </div>
                        <div className="text-right">
                          <span className="text-xl font-bold text-primary">
                            {contributionPercentage.toFixed(1)}%
                          </span>
                          <span className="text-xs text-muted-foreground ml-1">
                            ({contribution.toFixed(1)} pts)
                          </span>
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>Relative Impact</span>
                          <span>{contributionPercentage.toFixed(0)}% of total</span>
                        </div>
                        <div className="h-2 bg-secondary/50 rounded-full overflow-hidden">
                          <motion.div
                            className="h-full bg-gradient-to-r from-primary to-bubble-secondary"
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.min(contributionPercentage, 100)}%` }}
                            transition={{ duration: 0.5, ease: "easeOut" }}
                          />
                        </div>
                      </div>

                      <AnimatePresence>
                        {showExplanation && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                          >
                            <div className="p-3 mt-2 bg-secondary/30 rounded-lg border border-border/50">
                              <p className="text-xs text-muted-foreground leading-relaxed">
                                This category contributes <strong>{contributionPercentage.toFixed(1)}%</strong> to the overall bubble score. 
                                The contribution is calculated by multiplying the category's score ({getCategoryScore(category, true).toFixed(1)}) 
                                by your custom weight ({category.userWeight}%) and normalizing against the total score.
                                Market score for this category is {getMarketCategoryScore(category).toFixed(1)}.
                              </p>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                )}
              </div>

              {/* Advanced Mode: Factor Index Controls */}
              <AnimatePresence>
                {showAdvanced && isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="mt-6 pt-6 border-t border-border space-y-6 overflow-hidden"
                  >
                    {category.indexes.map((index) => {
                      const showIndexExplanation = showExplanations.has(index.id);
                      const currentValue = index.userValue ?? index.value;
                      
                      return (
                        <div key={index.id} className="space-y-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <h4 className="text-sm font-medium text-foreground">
                                  {index.name}
                                </h4>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-5 w-5 p-0"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    toggleExplanation(index.id);
                                  }}
                                >
                                  <Info className="w-3 h-3 text-muted-foreground" />
                                </Button>
                              </div>
                              <p className="text-xs text-muted-foreground mt-1">
                                {index.description}
                              </p>
                            </div>
                            <div className="text-right ml-4">
                              <div className="text-sm font-semibold text-primary">
                                {currentValue.toFixed(0)}%
                              </div>
                              <div className="text-xs text-muted-foreground">
                                Market: {index.value.toFixed(0)}%
                              </div>
                            </div>
                          </div>

                          {/* Factor Explanation */}
                          <AnimatePresence>
                            {showIndexExplanation && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.2 }}
                                className="overflow-hidden"
                              >
                                <div className="p-3 bg-primary/5 rounded-lg border border-primary/20">
                                  <p className="text-xs text-foreground leading-relaxed">
                                    {index.explanation}
                                  </p>
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>

                          {/* Factor Value Slider */}
                          <div>
                            <Slider
                              value={[currentValue]}
                              onValueChange={([value]) => {
                                if (onIndexValueChange) {
                                  onIndexValueChange(category.id, index.id, value);
                                }
                              }}
                              min={0}
                              max={100}
                              step={1}
                              className="mb-1"
                              disabled={readOnly}
                            />
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>0%</span>
                              <span>Market: {index.value}%</span>
                              <span>100%</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </motion.div>
                )}
              </AnimatePresence>
            </Card>
          );
        })}
      </div>
    </div>
  );
};