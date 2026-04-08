import useAuth from "@/hooks/useAuth"
import { getCapabilities } from "@/lib/capabilities"

const useCapabilities = () => {
  const { user } = useAuth()
  return getCapabilities(user?.role)
}

export default useCapabilities
