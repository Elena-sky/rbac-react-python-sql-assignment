import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"

import { MetricsService } from "@/client"
import { requireCapability } from "@/lib/route-guards"

function getMetricsQueryOptions() {
  return {
    queryFn: () => MetricsService.readMetricsStub(),
    queryKey: ["metrics"],
  }
}

export const Route = createFileRoute("/_layout/metrics")({
  component: Metrics,
  beforeLoad: async ({ location }) => {
    await requireCapability("canViewMetrics", location.pathname)
  },
  head: () => ({
    meta: [
      {
        title: "Metrics - FastAPI Template",
      },
    ],
  }),
})

function Metrics() {
  const { data, error, isPending } = useQuery(getMetricsQueryOptions())

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Metrics</h1>
        <p className="text-muted-foreground">System metrics snapshot</p>
      </div>

      {isPending ? <p>Loading metrics...</p> : null}

      {error ? <p>Failed to load metrics.</p> : null}

      {data ? (
        <pre className="rounded-md border bg-muted p-4 text-sm overflow-x-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      ) : null}
    </div>
  )
}
