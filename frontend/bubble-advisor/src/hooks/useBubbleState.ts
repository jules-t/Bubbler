import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import { BubbleState, MetricsData } from "@/types/api";
import { Category } from "@/types/bubble";
import { categoriesToMetrics } from "@/utils/dataMapper";

/**
 * Hook to fetch and cache bubble state from backend
 */
export function useBubbleState(bubbleId: string) {
  return useQuery<BubbleState>({
    queryKey: ["bubbleState", bubbleId],
    queryFn: () => apiClient.getBubbleStatus(bubbleId),
    staleTime: 30000, // Consider data fresh for 30 seconds
    retry: 2,
  });
}

/**
 * Hook to initialize or update bubble with new metrics
 */
export function useInitializeBubble() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      bubbleId,
      metrics,
    }: {
      bubbleId: string;
      metrics: MetricsData;
    }) => apiClient.initializeBubble(bubbleId, metrics),
    onSuccess: (data, variables) => {
      // Update the cached bubble state using bubbleId from request
      queryClient.setQueryData(["bubbleState", variables.bubbleId], data);
    },
  });
}

/**
 * Hook to initialize bubble from frontend categories
 */
export function useInitializeBubbleFromCategories() {
  const initializeBubble = useInitializeBubble();

  return {
    ...initializeBubble,
    initializeFromCategories: (
      bubbleId: string,
      categories: Category[],
      useUserValues: boolean = false
    ) => {
      const metrics = categoriesToMetrics(categories, useUserValues);
      return initializeBubble.mutate({ bubbleId, metrics });
    },
  };
}

/**
 * Hook to check backend health
 */
export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => apiClient.healthCheck(),
    staleTime: 60000, // Check every minute
    retry: 1,
  });
}
