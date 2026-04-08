import { EllipsisVertical } from "lucide-react"
import { useState } from "react"

import type { ItemPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import useCapabilities from "@/hooks/useCapabilities"
import DeleteItem from "../Items/DeleteItem"
import EditItem from "../Items/EditItem"

interface ItemActionsMenuProps {
  item: ItemPublic
}

export const ItemActionsMenu = ({ item }: ItemActionsMenuProps) => {
  const [open, setOpen] = useState(false)
  const { canEditItem, canDeleteItem } = useCapabilities()

  if (!canEditItem && !canDeleteItem) {
    return null
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {canEditItem ? (
          <EditItem item={item} onSuccess={() => setOpen(false)} />
        ) : null}
        {canDeleteItem ? (
          <DeleteItem id={item.id} onSuccess={() => setOpen(false)} />
        ) : null}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
