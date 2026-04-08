import type { UserRole } from "@/client"

export type Capabilities = {
  canManageUsers: boolean
  canCreateUser: boolean
  canViewMetrics: boolean
  canEditOwnProfile: boolean
  canEditAnyProfile: boolean
}

const defaultCapabilities: Capabilities = {
  canManageUsers: false,
  canCreateUser: false,
  canViewMetrics: false,
  canEditOwnProfile: false,
  canEditAnyProfile: false,
}

const capabilitiesByRole: Record<UserRole, Capabilities> = {
  admin: {
    canManageUsers: true,
    canCreateUser: true,
    canViewMetrics: true,
    canEditOwnProfile: true,
    canEditAnyProfile: true,
  },
  manager: {
    canManageUsers: true,
    canCreateUser: false,
    canViewMetrics: true,
    canEditOwnProfile: true,
    canEditAnyProfile: false,
  },
  member: {
    canManageUsers: false,
    canCreateUser: false,
    canViewMetrics: false,
    canEditOwnProfile: true,
    canEditAnyProfile: false,
  },
}

export const getCapabilities = (
  role: UserRole | null | undefined,
): Capabilities => {
  if (!role) {
    return defaultCapabilities
  }

  return capabilitiesByRole[role] ?? defaultCapabilities
}
