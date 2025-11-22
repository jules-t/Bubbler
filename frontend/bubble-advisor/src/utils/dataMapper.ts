import { Category, Index } from "@/types/bubble";
import { MetricsData } from "@/types/api";

/**
 * Transform frontend Category[] to backend MetricsData
 * Maps user-adjusted or market values from categories to backend metric structure
 */
export function categoriesToMetrics(
  categories: Category[],
  useUserValues: boolean = false
): MetricsData {
  const valuation = categories.find((c) => c.id === "valuation");
  const sentiment = categories.find((c) => c.id === "sentiment");
  const positioning = categories.find((c) => c.id === "positioning");
  const macro = categories.find((c) => c.id === "macro");
  const fundamentals = categories.find((c) => c.id === "fundamentals");

  if (!valuation || !sentiment || !positioning || !macro || !fundamentals) {
    throw new Error("Missing required categories");
  }

  // Helper to get value from index (user value if available and requested, otherwise market value)
  const getValue = (index: Index): number => {
    if (useUserValues && index.userValue !== undefined) {
      return index.userValue;
    }
    return index.value;
  };

  // Helper to find index by id
  const findIndex = (category: Category, id: string): Index => {
    const index = category.indexes.find((i) => i.id === id);
    if (!index) {
      throw new Error(`Index ${id} not found in category ${category.id}`);
    }
    return index;
  };

  return {
    category_1_valuation: {
      pe_ratio: getValue(findIndex(valuation, "pe-ratio")),
      revenue_multiple: getValue(findIndex(valuation, "revenue-multiple")),
      market_cap_gdp: getValue(findIndex(valuation, "market-cap")),
      growth_premium: getValue(findIndex(valuation, "growth-premium")),
    },
    category_2_sentiment: {
      media_mentions: getValue(findIndex(sentiment, "media-mentions")),
      social_sentiment: getValue(findIndex(sentiment, "social-sentiment")),
      search_trends: getValue(findIndex(sentiment, "search-trends")),
      analyst_ratings: getValue(findIndex(sentiment, "analyst-ratings")),
      ipo_activity: getValue(findIndex(sentiment, "ipo-activity")),
    },
    category_3_positioning: {
      fund_flows: getValue(findIndex(positioning, "fund-flows")),
      institutional_holdings: getValue(findIndex(positioning, "institutional")),
      retail_interest: getValue(findIndex(positioning, "retail-interest")),
      options_volume: getValue(findIndex(positioning, "options-volume")),
    },
    category_4_macro: {
      interest_rates: getValue(findIndex(macro, "interest-rates")),
      liquidity: getValue(findIndex(macro, "liquidity")),
      vix: getValue(findIndex(macro, "vix")),
      put_call_ratio: getValue(findIndex(macro, "put-call")),
    },
    category_5_fundamentals: {
      revenue_growth: getValue(findIndex(fundamentals, "revenue-growth")),
      profit_margins: getValue(findIndex(fundamentals, "profit-margins")),
      capex_cycle: getValue(findIndex(fundamentals, "capex-cycle")),
      adoption_rate: getValue(findIndex(fundamentals, "adoption-rate")),
      competition: getValue(findIndex(fundamentals, "competition")),
    },
  };
}

/**
 * Calculate weighted average risk score from categories
 * This is a client-side approximation - the backend will do the official calculation
 */
export function calculateClientRiskScore(
  categories: Category[],
  useUserValues: boolean = false
): number {
  let totalScore = 0;
  let totalWeight = 0;

  categories.forEach((category) => {
    const weight = useUserValues ? category.userWeight : category.marketWeight;
    let categoryScore = 0;
    let categoryIndexWeight = 0;

    category.indexes.forEach((index) => {
      const value = useUserValues && index.userValue !== undefined
        ? index.userValue
        : index.value;
      const indexWeight = useUserValues ? 1 : index.marketWeight || 1; // Equal weight for user mode
      categoryScore += value * indexWeight;
      categoryIndexWeight += indexWeight;
    });

    if (categoryIndexWeight > 0) {
      categoryScore = categoryScore / categoryIndexWeight;
    }

    totalScore += categoryScore * weight;
    totalWeight += weight;
  });

  return totalWeight > 0 ? totalScore / totalWeight : 0;
}

/**
 * Determine risk level based on score
 */
export function getRiskLevel(score: number): "LOW" | "MEDIUM" | "HIGH" {
  if (score < 33) return "LOW";
  if (score < 67) return "MEDIUM";
  return "HIGH";
}
