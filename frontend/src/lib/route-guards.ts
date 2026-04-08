import { redirect } from "@tanstack/react-router"

import { UsersService } from "@/client"
import { isLoggedIn } from "@/hooks/useAuth"
import type { Capabilities } from "@/lib/capabilities"
import { getCapabilities } from "@/lib/capabilities"

type CapabilityKey = keyof Capabilities

export const requireAuth = () => {
  if (!isLoggedIn()) {
    throw redirect({ to: "/login" })
  }
}

export const requireCapability = async (
  capability: CapabilityKey,
  pathname?: string,
) => {
  if (pathname === "/forbidden") {
    return
  }

  const user = await UsersService.readUserMe()
  const capabilities = getCapabilities(user.role)

  if (!capabilities[capability]) {
    throw redirect({ to: "/forbidden" })
  }
}
