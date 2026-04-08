import { Link } from "@tanstack/react-router"

import { Button } from "@/components/ui/button"

const Forbidden = () => {
  return (
    <div
      className="flex min-h-[60vh] items-center justify-center flex-col p-4"
      data-testid="forbidden-component"
    >
      <div className="flex items-center z-10">
        <div className="flex flex-col ml-4 items-center justify-center p-4">
          <span className="text-6xl md:text-8xl font-bold leading-none mb-4">
            403
          </span>
          <span className="text-2xl font-bold mb-2">Access Denied</span>
        </div>
      </div>
      <p className="text-lg text-muted-foreground mb-4 text-center z-10">
        You do not have permission to access this section.
      </p>
      <div className="flex gap-2 z-10">
        <Button
          variant="outline"
          onClick={() => {
            window.history.back()
          }}
        >
          Go Back
        </Button>
        <Link to="/">
          <Button>Go Home</Button>
        </Link>
      </div>
    </div>
  )
}

export default Forbidden
