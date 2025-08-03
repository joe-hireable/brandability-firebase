import { cva } from "class-variance-authority"

// The base button class that all buttons will share
const baseButtonClass = "btn inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50"

export const buttonVariants = cva(baseButtonClass, {
  variants: {
    variant: {
      default: "btn-primary",
      destructive: "bg-brand-error text-white hover:bg-opacity-90",
      outline: "border border-gray-300 bg-white text-gray-700 hover:bg-brand-secondary hover:text-brand-primary",
      secondary: "btn-secondary",
      ghost: "bg-transparent hover:bg-brand-secondary hover:text-brand-primary",
      link: "bg-transparent text-brand-primary hover:text-brand-accent underline-offset-4 hover:underline p-0",
      accent: "btn-accent",
      success: "bg-brand-success text-white hover:bg-opacity-90",
      warning: "bg-brand-warning text-white hover:bg-opacity-90",
      legal: "border border-brand-primary text-brand-primary bg-white hover:bg-brand-secondary font-serif",
    },
    size: {
      default: "h-10 px-5 py-2.5",
      sm: "h-8 rounded-md px-3 py-2 text-xs",
      lg: "h-12 rounded-lg px-8 py-3 text-base",
      icon: "h-10 w-10 p-0",
    },
  },
  defaultVariants: {
    variant: "default",
    size: "default",
  },
})