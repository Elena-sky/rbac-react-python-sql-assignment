import { expect, test } from "@playwright/test"

import { getCapabilities } from "../src/lib/capabilities"

test.describe("capabilities model", () => {
  test("maps admin role to full management capabilities", () => {
    expect(getCapabilities("admin")).toEqual({
      canManageUsers: true,
      canCreateUser: true,
      canViewMetrics: true,
      canEditOwnProfile: true,
      canEditAnyProfile: true,
      canCreateItem: true,
      canEditItem: true,
      canDeleteItem: true,
    })
  })

  test("maps manager role to limited management capabilities", () => {
    expect(getCapabilities("manager")).toEqual({
      canManageUsers: true,
      canCreateUser: false,
      canViewMetrics: true,
      canEditOwnProfile: true,
      canEditAnyProfile: false,
      canCreateItem: true,
      canEditItem: true,
      canDeleteItem: true,
    })
  })

  test("maps member role to own-profile only capabilities", () => {
    expect(getCapabilities("member")).toEqual({
      canManageUsers: false,
      canCreateUser: false,
      canViewMetrics: false,
      canEditOwnProfile: true,
      canEditAnyProfile: false,
      canCreateItem: true,
      canEditItem: true,
      canDeleteItem: true,
    })
  })

  test("returns safe all-false fallback for null and undefined roles", () => {
    expect(getCapabilities(null)).toEqual({
      canManageUsers: false,
      canCreateUser: false,
      canViewMetrics: false,
      canEditOwnProfile: false,
      canEditAnyProfile: false,
      canCreateItem: false,
      canEditItem: false,
      canDeleteItem: false,
    })
    expect(getCapabilities(undefined)).toEqual({
      canManageUsers: false,
      canCreateUser: false,
      canViewMetrics: false,
      canEditOwnProfile: false,
      canEditAnyProfile: false,
      canCreateItem: false,
      canEditItem: false,
      canDeleteItem: false,
    })
  })
})
