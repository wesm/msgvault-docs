import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://msgvault.io',
  integrations: [
    starlight({
      title: 'msgvault',
      disable404Route: false,
      components: {
        ThemeSelect: './src/components/EmptyThemeSelect.astro',
        Header: './src/components/Header.astro',
        Footer: './src/components/Footer.astro',
      },
      social: {
        discord: 'https://discord.gg/fDnmxB8Wkq',
      },
      customCss: ['./src/styles/custom.css'],
      expressiveCode: {
        themes: ['github-dark-dimmed'],
        styleOverrides: {
          copyButton: {
            visible: true,
          },
        },
      },
      head: [
        {
          tag: 'script',
          attrs: { src: '/lightbox.js', defer: true },
        },
        {
          tag: 'meta',
          attrs: { property: 'og:type', content: 'website' },
        },
        {
          tag: 'meta',
          attrs: { property: 'og:image', content: 'https://msgvault.io/og-image.png' },
        },
        {
          tag: 'meta',
          attrs: { property: 'og:image:width', content: '1200' },
        },
        {
          tag: 'meta',
          attrs: { property: 'og:image:height', content: '630' },
        },
        {
          tag: 'meta',
          attrs: { name: 'twitter:card', content: 'summary_large_image' },
        },
        {
          tag: 'meta',
          attrs: { name: 'twitter:image', content: 'https://msgvault.io/og-image.png' },
        },
      ],
      sidebar: [
        { label: 'Introduction', slug: 'introduction' },
        { label: 'Setup Guide', slug: 'setup' },
        { label: 'Interactive TUI', slug: 'usage/tui' },
        { label: 'Configuration', slug: 'configuration' },
        { label: 'CLI Reference', slug: 'cli-reference' },
        { label: 'MCP Server', slug: 'usage/chat' },
        { label: 'Web Server', slug: 'api-server' },
        {
          label: 'CLI Usage',
          items: [
            { label: 'Searching', slug: 'usage/searching' },
            { label: 'Importing Local Email', slug: 'usage/importing' },
            { label: 'Exporting Data', slug: 'usage/exporting' },
            { label: 'Analytics & Stats', slug: 'usage/analytics' },
            { label: 'Deleting Email', slug: 'usage/deletion' },
            { label: 'Multi-Account', slug: 'usage/multi-account' },
          ],
        },
        {
          label: 'Guides',
          items: [
            { label: 'Google OAuth Setup', slug: 'guides/oauth-setup' },
{ label: 'Verify Integrity', slug: 'guides/verification' },
          ],
        },
        {
          label: 'Architecture',
          items: [
            { label: 'Overview', slug: 'architecture/overview' },
            { label: 'Data Storage', slug: 'architecture/storage' },
          ],
        },
        { label: 'Troubleshooting', slug: 'troubleshooting' },
        { label: 'Development', slug: 'development' },
        { label: 'FAQ', slug: 'faq' },
      ],
    }),
  ],
});
