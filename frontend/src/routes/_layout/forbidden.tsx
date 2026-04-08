import { createFileRoute } from "@tanstack/react-router"

import Forbidden from "@/components/Common/Forbidden"

export const Route = createFileRoute("/_layout/forbidden")({
  component: ForbiddenPage,
  head: () => ({
    meta: [
      {
        title: "Forbidden - FastAPI Template",
      },
    ],
  }),
})

function ForbiddenPage() {
  return <Forbidden />
}
