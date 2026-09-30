const path = require('path')

let frappeUiSrc
try {
  frappeUiSrc = path.dirname(require.resolve('frappe-ui/style.css'))
} catch (e) {
  frappeUiSrc = path.resolve(__dirname, '../../node_modules/frappe-ui/src')
}
const frappeUiFrappe = path.join(path.dirname(frappeUiSrc), 'frappe')

module.exports = {
  presets: [
    require('frappe-ui/tailwind')
  ],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    `${frappeUiSrc}/**/*.{vue,js,ts,jsx,tsx}`,
    `${frappeUiFrappe}/**/*.{vue,js,ts,jsx,tsx}`,
  ],
  plugins: [],
}
