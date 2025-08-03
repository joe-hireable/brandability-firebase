import { Button } from './components/ui/button';

const DesignSystem = () => {
  const colors = [
    { name: 'Primary', value: 'bg-brand-primary', text: 'text-white' },
    { name: 'Secondary', value: 'bg-brand-secondary', text: 'text-brand-primary' },
    { name: 'Accent', value: 'bg-brand-accent', text: 'text-white' },
    { name: 'Success', value: 'bg-brand-success', text: 'text-white' },
    { name: 'Warning', value: 'bg-brand-warning', text: 'text-white' },
    { name: 'Error', value: 'bg-brand-error', text: 'text-white' },
    { name: 'Text Primary', value: 'bg-brand-text-primary', text: 'text-white' },
    { name: 'Text Secondary', value: 'bg-brand-text-secondary', text: 'text-white' },
    { name: 'Neutral Gray', value: 'bg-brand-neutral-gray', text: 'text-brand-primary' },
  ];

  const buttonVariantNames = [
    'default',
    'secondary',
    'accent',
    'destructive',
    'outline',
    'ghost',
    'link',
    'success',
    'warning',
    'legal'
  ] as const;

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <h1 className="mb-8">Brandability Design System</h1>
      <p className="text-brand-text-secondary mb-12">
        A comprehensive design system for the Brandability application, tailored for trademark lawyers.
      </p>

      {/* Typography */}
      <section className="mb-16">
        <h2 className="mb-6">Typography</h2>
        <div className="space-y-6">
          <div>
            <h1>Heading 1 - Merriweather Bold</h1>
            <p className="text-sm text-brand-text-secondary mt-2">Used for main page titles</p>
          </div>
          <div>
            <h2>Heading 2 - Merriweather Bold</h2>
            <p className="text-sm text-brand-text-secondary mt-2">Used for section headings</p>
          </div>
          <div>
            <h3>Heading 3 - Merriweather Bold</h3>
            <p className="text-sm text-brand-text-secondary mt-2">Used for subsection headings</p>
          </div>
          <div>
            <h4>Heading 4 - Merriweather Bold</h4>
            <p className="text-sm text-brand-text-secondary mt-2">Used for card headings</p>
          </div>
          <div>
            <h5>Heading 5 - Merriweather Bold</h5>
            <p className="text-sm text-brand-text-secondary mt-2">Used for minor headings</p>
          </div>
          <div>
            <h6>Heading 6 - Merriweather Bold</h6>
            <p className="text-sm text-brand-text-secondary mt-2">Used for the smallest headings</p>
          </div>
          <div>
            <p className="text-lg">Large Text - Open Sans Regular</p>
            <p className="text-sm text-brand-text-secondary mt-2">Used for important paragraphs and introductions</p>
          </div>
          <div>
            <p>Body Text - Open Sans Regular</p>
            <p className="text-sm text-brand-text-secondary mt-2">The default text style for paragraphs and general content</p>
          </div>
          <div>
            <p className="text-sm">Small Text - Open Sans Regular</p>
            <p className="text-sm text-brand-text-secondary mt-2">Used for captions, footnotes, and secondary information</p>
          </div>
          <div>
            <a href="#" className="text-brand-primary hover:text-brand-accent">Link Text - Open Sans Regular</a>
            <p className="text-sm text-brand-text-secondary mt-2">Used for links and interactive text elements</p>
          </div>
          <div>
            <blockquote className="pl-4 border-l-4 border-brand-accent italic text-brand-text-secondary">
              Blockquote - Open Sans Italic
            </blockquote>
            <p className="text-sm text-brand-text-secondary mt-2">Used for quotations and citations</p>
          </div>
          <div>
            <code className="bg-brand-secondary rounded px-1 py-0.5 text-sm">Code Text - Monospace</code>
            <p className="text-sm text-brand-text-secondary mt-2">Used for code snippets and technical information</p>
          </div>
        </div>
      </section>

      {/* Colors */}
      <section className="mb-16">
        <h2 className="mb-6">Color Palette</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {colors.map((color) => (
            <div 
              key={color.name}
              className={`p-6 rounded-lg ${color.value} ${color.text} shadow-sm`}
            >
              <div className="flex justify-between items-center">
                <span className="font-medium">{color.name}</span>
                <code className="text-xs">{color.value.replace('bg-', '')}</code>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Buttons */}
      <section className="mb-16">
        <h2 className="mb-6">Buttons</h2>
        
        <h3 className="mb-4">Button Variants</h3>
        <div className="flex flex-wrap gap-4 mb-8">
          {buttonVariantNames.map((variant) => (
            <Button key={variant} variant={variant}>
              {variant.charAt(0).toUpperCase() + variant.slice(1)}
            </Button>
          ))}
        </div>

        <h3 className="mb-4">Button Sizes</h3>
        <div className="flex flex-wrap gap-4 items-center">
          <Button size="sm">Small Button</Button>
          <Button size="default">Default Button</Button>
          <Button size="lg">Large Button</Button>
          <Button size="icon">🔍</Button>
        </div>
      </section>

      {/* Card Example */}
      <section className="mb-16">
        <h2 className="mb-6">Card Examples</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card-trademark">
            <h4 className="mb-2">Trademark Application</h4>
            <p className="text-brand-text-secondary mb-4">A sample trademark application card.</p>
            <div className="flex justify-between items-center">
              <span className="badge-status badge-status-pending">Pending</span>
              <Button variant="secondary" size="sm">View Details</Button>
            </div>
          </div>

          <div className="card-trademark">
            <h4 className="mb-2">Registered Trademark</h4>
            <p className="text-brand-text-secondary mb-4">A sample registered trademark card.</p>
            <div className="flex justify-between items-center">
              <span className="badge-status badge-status-approved">Approved</span>
              <Button variant="secondary" size="sm">View Details</Button>
            </div>
          </div>
        </div>
      </section>

      {/* Form Elements (Placeholder) */}
      <section className="mb-16">
        <h2 className="mb-6">Form Elements</h2>
        <p className="text-brand-text-secondary mb-4">
          Form elements will follow the same design principles, with clear labels, accessible inputs, and consistent styling.
        </p>
        <div className="card-trademark p-6">
          <p className="text-sm text-brand-text-secondary mb-4">
            Form controls will be added as the design system expands.
          </p>
        </div>
      </section>

      {/* Legal-specific Elements */}
      <section className="mb-16">
        <h2 className="mb-6">Legal-specific Elements</h2>
        <div className="container-legal bg-white p-6 rounded-lg border border-brand-secondary">
          <h3 className="legal-heading">Sample Legal Document Section</h3>
          <div className="legal-section">
            <p className="mb-2">This showcases how legal documents would be styled within the application.</p>
            <p className="mb-4">The typography, spacing, and overall layout are designed for optimal readability when working with legal content.</p>
            <Button variant="legal">Legal Action</Button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default DesignSystem;