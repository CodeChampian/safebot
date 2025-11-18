// Simplified form components for basic form handling
import * as React from "react"

const Form = ({ children, onSubmit, className, ...props }) => {
  const handleSubmit = (e) => {
    e.preventDefault()
    if (onSubmit) {
      onSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className={className} {...props}>
      {children}
    </form>
  )
}

const FormField = ({ children, ...props }) => (
  <div {...props}>
    {children}
  </div>
)

const FormItem = ({ children, className, ...props }) => (
  <div className={`space-y-2 ${className || ''}`} {...props}>
    {children}
  </div>
)

const FormLabel = ({ children, className, ...props }) => (
  <label className={`text-sm font-medium ${className || ''}`} {...props}>
    {children}
  </label>
)

const FormControl = ({ children }) => (
  <div>
    {children}
  </div>
)

const FormMessage = ({ error, className }) => (
  error ? (
    <p className={`text-sm text-red-600 ${className || ''}`}>
      {error}
    </p>
  ) : null
)

export { Form, FormField, FormItem, FormLabel, FormControl, FormMessage }
