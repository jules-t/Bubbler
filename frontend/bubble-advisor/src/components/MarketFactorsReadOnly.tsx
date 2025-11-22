import { Card } from "@/components/ui/card";
import { Category } from "@/types/bubble";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface MarketFactorsReadOnlyProps {
  categories: Category[];
}

export const MarketFactorsReadOnly = ({ categories }: MarketFactorsReadOnlyProps) => {
  const getValueIndicator = (value: number) => {
    if (value >= 70) return { icon: TrendingUp, color: "text-bubble-danger", label: "High Risk" };
    if (value >= 50) return { icon: Minus, color: "text-bubble-warning", label: "Elevated" };
    return { icon: TrendingDown, color: "text-bubble-safe", label: "Moderate" };
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-primary">Market Consensus Factors</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Current market conditions based on real-time data and analysis
        </p>
      </div>

      <div className="space-y-4">
        {categories.map((category, idx) => {
          const avgValue = category.indexes.reduce((sum, index) => sum + index.value, 0) / category.indexes.length;
          const indicator = getValueIndicator(avgValue);
          const Icon = indicator.icon;

          return (
            <motion.div
              key={category.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.1 }}
            >
              <Card className="p-6 bg-card border-border">
                <div className="space-y-4">
                  {/* Category Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-foreground">
                          {category.name}
                        </h3>
                        <div className={`flex items-center gap-1 ${indicator.color}`}>
                          <Icon className="w-4 h-4" />
                          <span className="text-xs font-medium">{indicator.label}</span>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {category.description}
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <div className="text-3xl font-bold text-primary">
                        {avgValue.toFixed(0)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Current Level
                      </div>
                    </div>
                  </div>

                  {/* Category Explanation */}
                  <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                    <p className="text-sm text-foreground leading-relaxed">
                      {category.explanation}
                    </p>
                  </div>

                  {/* Individual Factors */}
                  <div className="space-y-3 pt-2">
                    <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                      Contributing Factors
                    </div>
                    {category.indexes.map((index) => {
                      const indexIndicator = getValueIndicator(index.value);
                      const IndexIcon = indexIndicator.icon;

                      return (
                        <div key={index.id} className="space-y-2">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <h4 className="text-sm font-medium text-foreground">
                                  {index.name}
                                </h4>
                                <IndexIcon className={`w-3 h-3 ${indexIndicator.color}`} />
                              </div>
                              <p className="text-xs text-muted-foreground">
                                {index.description}
                              </p>
                            </div>
                            <div className="text-right ml-4">
                              <div className="text-lg font-bold text-primary">
                                {index.value.toFixed(0)}
                              </div>
                            </div>
                          </div>
                          
                          {/* Visual indicator bar */}
                          <div className="h-1.5 bg-secondary/50 rounded-full overflow-hidden">
                            <motion.div
                              className={`h-full ${
                                index.value >= 70 ? 'bg-bubble-danger' :
                                index.value >= 50 ? 'bg-bubble-warning' :
                                'bg-bubble-safe'
                              }`}
                              initial={{ width: 0 }}
                              animate={{ width: `${index.value}%` }}
                              transition={{ duration: 0.8, delay: idx * 0.1 + 0.3 }}
                            />
                          </div>

                          {/* Factor Explanation */}
                          <div className="p-3 bg-secondary/30 rounded-lg border border-border/50">
                            <p className="text-xs text-foreground leading-relaxed">
                              <span className="font-semibold">Why this matters:</span> {index.explanation}
                            </p>
                            <div className="mt-2 pt-2 border-t border-border/50">
                              <p className="text-xs text-muted-foreground">
                                <span className="font-semibold">Current level ({index.value}):</span>{" "}
                                {index.value >= 70 
                                  ? "Indicates elevated bubble risk in this area. Historical patterns suggest heightened vulnerability."
                                  : index.value >= 50
                                  ? "Shows moderate concerns. Worth monitoring but not at critical levels yet."
                                  : "Remains within healthy ranges. No immediate concerns for bubble formation."}
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
