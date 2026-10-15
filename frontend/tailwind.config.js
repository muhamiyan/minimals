const { content: frappeUiContent } = require('frappe-ui/tailwind')

module.exports = {
  presets: [
    require('frappe-ui/tailwind')
  ],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    ...frappeUiContent,
  ],
  plugins: [],
}
