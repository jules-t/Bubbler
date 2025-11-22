export interface Index {
  id: string;
  name: string;
  description: string;
  value: number; // 0-100
  marketWeight: number; // 0-100
  userValue?: number; // User's custom value in advanced mode
  explanation: string; // Why this factor matters and what current level means
}

export interface Category {
  id: string;
  name: string;
  description: string;
  indexes: Index[];
  userWeight: number; // User's custom weight 0-100
  marketWeight: number; // Market consensus weight 0-100
  explanation: string; // What this category means and current market implications
}

export const CATEGORIES: Category[] = [
  {
    id: "valuation",
    name: "Market Valuation",
    description: "Price metrics vs historical norms",
    explanation: "Market valuation measures how expensive AI stocks are relative to their earnings and revenue. High valuations (85%+) suggest investors are pricing in significant future growth, potentially creating bubble conditions if expectations aren't met. Current market consensus shows elevated valuations near historical peaks, indicating strong optimism but also increased risk.",
    marketWeight: 50,
    userWeight: 50,
    indexes: [
      {
        id: "pe-ratio",
        name: "AI Stock P/E Ratio",
        description: "Price-to-earnings ratio vs historical average",
        explanation: "P/E ratios show how much investors pay per dollar of earnings. At 85%, AI stocks are trading at premiums significantly above historical tech sector averages, suggesting very high growth expectations are already priced in.",
        value: 85,
        marketWeight: 12.5,
      },
      {
        id: "revenue-multiple",
        name: "Revenue Multiples",
        description: "Price-to-sales ratios for AI companies",
        explanation: "Revenue multiples indicate how the market values each dollar of sales. At 78%, these multiples are elevated but justified if AI companies can maintain rapid revenue growth. A decline in growth rates could trigger sharp repricing.",
        value: 78,
        marketWeight: 12.5,
      },
      {
        id: "market-cap",
        name: "Market Cap / GDP",
        description: "AI sector size relative to economy",
        explanation: "This ratio compares the AI sector's total value to economic output. At 68%, the AI sector represents a meaningful portion of GDP, though not yet at dot-com bubble extremes. Further expansion depends on real economic impact.",
        value: 68,
        marketWeight: 12.5,
      },
      {
        id: "growth-premium",
        name: "Growth Premium",
        description: "Valuation premium for growth expectations",
        explanation: "Growth premium reflects how much extra investors pay for expected future growth. At 82%, the market is pricing in aggressive expansion scenarios. If growth disappoints, this premium could compress quickly.",
        value: 82,
        marketWeight: 12.5,
      },
    ],
  },
  {
    id: "sentiment",
    name: "Sentiment & Hype",
    description: "Market excitement and media coverage",
    explanation: "Sentiment measures the emotional and psychological enthusiasm around AI investments. Extremely high sentiment (90%+) often precedes corrections as hype exceeds reality. Current levels show strong excitement with media coverage near peak levels, suggesting we're in the euphoric phase where retail participation surges.",
    marketWeight: 50,
    userWeight: 50,
    indexes: [
      {
        id: "media-mentions",
        name: "Media Mentions",
        description: "AI coverage in major publications",
        explanation: "Media coverage intensity often peaks near market tops. At 92%, AI dominates financial news cycles, similar to internet stocks in 1999. This saturation can signal we're late in the hype cycle.",
        value: 92,
        marketWeight: 10,
      },
      {
        id: "social-sentiment",
        name: "Social Sentiment",
        description: "Social media discussion volume",
        explanation: "Social media buzz tracks retail investor interest. At 88%, discussion volumes are extremely elevated, indicating widespread public participation—typically a late-stage bull market signal.",
        value: 88,
        marketWeight: 10,
      },
      {
        id: "search-trends",
        name: "Search Trends",
        description: "Google search interest in AI stocks",
        explanation: "Search volume shows public curiosity and FOMO. At 75%, search interest is high but not yet at mania levels. A spike above 90% would suggest maximum retail interest and potential reversal.",
        value: 75,
        marketWeight: 10,
      },
      {
        id: "analyst-ratings",
        name: "Analyst Ratings",
        description: "Buy/sell recommendations ratio",
        explanation: "Analyst sentiment reflects Wall Street's view. At 80%, most analysts are bullish, which can be contrarian bearish when consensus becomes too one-sided. Few dissenting voices suggests complacency.",
        value: 80,
        marketWeight: 10,
      },
      {
        id: "ipo-activity",
        name: "IPO Activity",
        description: "New AI company listings",
        explanation: "IPO waves indicate companies rushing to market to capture high valuations. At 70%, activity is elevated but not at frenzy levels. Acceleration above 85% would signal peak euphoria.",
        value: 70,
        marketWeight: 10,
      },
    ],
  },
  {
    id: "positioning",
    name: "Positioning & Flows",
    description: "Investor positioning and capital flows",
    explanation: "Positioning tracks where investors are actually putting their money. Extreme positioning (80%+) can signal overcrowding and vulnerability to sharp reversals. Current flows show strong institutional and retail commitment, but this concentration increases systemic risk if sentiment shifts.",
    marketWeight: 50,
    userWeight: 50,
    indexes: [
      {
        id: "fund-flows",
        name: "Fund Flows",
        description: "Money flowing into AI ETFs",
        explanation: "Fund flows show institutional money movement. At 72%, steady inflows support prices but also create crowded trades. When flows reverse, forced selling can amplify downside moves.",
        value: 72,
        marketWeight: 10,
      },
      {
        id: "institutional",
        name: "Institutional Holdings",
        description: "Big money allocation to AI",
        explanation: "Institutional ownership indicates smart money positioning. At 68%, institutions have meaningful exposure but aren't yet overweight. Above 80% would suggest limited buying power remains.",
        value: 68,
        marketWeight: 10,
      },
      {
        id: "retail-interest",
        name: "Retail Interest",
        description: "Individual investor participation",
        explanation: "Retail participation often peaks at market tops. At 85%, individual investors are heavily engaged, suggesting we're in the distribution phase where institutions may be selling to retail.",
        value: 85,
        marketWeight: 10,
      },
      {
        id: "options-volume",
        name: "Options Volume",
        description: "Derivatives market activity",
        explanation: "Options activity shows speculation intensity. At 76%, volumes are elevated with bullish positioning. Extreme call buying above 85% typically precedes short-term corrections.",
        value: 76,
        marketWeight: 10,
      },
    ],
  },
  {
    id: "macro",
    name: "Macro & Liquidity",
    description: "Economic environment and capital availability",
    explanation: "Macro conditions determine how much money is available to chase assets. Low rates and high liquidity (below 60% on fear indicators) fuel speculation. Current conditions show moderate support with some caution, but any liquidity tightening could trigger rapid derating.",
    marketWeight: 50,
    userWeight: 50,
    indexes: [
      {
        id: "interest-rates",
        name: "Interest Rates",
        description: "Fed policy and rate expectations",
        explanation: "Interest rates determine the cost of capital. At 55%, rates are moderately supportive—not extremely low but not restrictive. Further hikes could pressure valuations as the discount rate rises.",
        value: 55,
        marketWeight: 10,
      },
      {
        id: "liquidity",
        name: "Market Liquidity",
        description: "M2 money supply and credit conditions",
        explanation: "Liquidity measures money available for investment. At 65%, conditions are adequate but not excessive. Bubbles typically require abundant liquidity above 80% to sustain momentum.",
        value: 65,
        marketWeight: 10,
      },
      {
        id: "vix",
        name: "VIX Fear Index",
        description: "Market volatility and fear indicator",
        explanation: "VIX measures market fear. At 68%, volatility is contained but not complacent. Readings below 50% signal extreme complacency, while above 80% indicates crisis.",
        value: 68,
        marketWeight: 12.5,
      },
      {
        id: "put-call",
        name: "Put/Call Ratio",
        description: "Options market sentiment",
        explanation: "Put/call ratio shows hedging behavior. At 72%, there's moderate caution—not excessive fear but not complacency either. Extreme readings (<40% or >90%) signal turning points.",
        value: 72,
        marketWeight: 12.5,
      },
    ],
  },
  {
    id: "fundamentals",
    name: "AI Infra Cycles & Profitability",
    description: "Business fundamentals and infrastructure",
    explanation: "Fundamentals show whether AI businesses can justify their valuations through real profits and growth. Strong fundamentals (70%+) can support high valuations, but if revenue growth slows or margins compress, the market could reprice aggressively. Current metrics show strong growth but mixed profitability.",
    marketWeight: 50,
    userWeight: 50,
    indexes: [
      {
        id: "revenue-growth",
        name: "Revenue Growth",
        description: "YoY revenue acceleration",
        explanation: "Revenue growth validates market enthusiasm. At 88%, growth is exceptionally strong, supporting high valuations. However, this pace is difficult to sustain—any deceleration could trigger sharp selloffs.",
        value: 88,
        marketWeight: 10,
      },
      {
        id: "profit-margins",
        name: "Profit Margins",
        description: "Operating and net margins",
        explanation: "Margins show business quality. At 62%, profitability is moderate—strong revenue growth hasn't fully translated to profits. Margin expansion would validate valuations; compression would raise concerns.",
        value: 62,
        marketWeight: 10,
      },
      {
        id: "capex-cycle",
        name: "CapEx Cycle",
        description: "Infrastructure investment phase",
        explanation: "CapEx spending indicates infrastructure build-out phase. At 78%, heavy investment supports long-term potential but pressures near-term margins. Peak CapEx often precedes overcapacity and corrections.",
        value: 78,
        marketWeight: 10,
      },
      {
        id: "adoption-rate",
        name: "Enterprise Adoption",
        description: "Corporate AI implementation rate",
        explanation: "Enterprise adoption validates real-world utility. At 70%, deployment is accelerating but not yet universal. Widespread adoption above 85% would justify optimism; stalling below 60% would be concerning.",
        value: 70,
        marketWeight: 10,
      },
      {
        id: "competition",
        name: "Competitive Intensity",
        description: "Market saturation and rivalry",
        explanation: "Competition determines pricing power and margins. At 75%, rivalry is intensifying as more players enter. Above 80% signals oversupply risk where excess capacity could compress profitability.",
        value: 75,
        marketWeight: 5,
      },
    ],
  },
];