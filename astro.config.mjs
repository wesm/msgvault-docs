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
        { label: 'Quick Start', slug: 'quickstart' },
        { label: 'Installation', slug: 'installation' },
        { label: 'Configuration', slug: 'configuration' },
        { label: 'CLI Reference', slug: 'cli-reference' },
        { label: 'Interactive TUI', slug: 'usage/tui' },
        {
          label: 'Usage',
          items: [
            { label: 'Syncing Email', slug: 'usage/syncing' },
            { label: 'Searching', slug: 'usage/searching' },
            { label: 'Exporting Messages', slug: 'usage/exporting' },
            { label: 'Analytics & Stats', slug: 'usage/analytics' },
            { label: 'LLM Chat', slug: 'usage/chat' },
            { label: 'MCP Server', slug: 'usage/mcp-server' },
            { label: 'Deleting Email', slug: 'usage/deletion' },
            { label: 'Multi-Account', slug: 'usage/multi-account' },
          ],
        },
        {
          label: 'Guides',
          items: [
            { label: 'Google OAuth Setup', slug: 'guides/oauth-setup' },
            { label: 'Headless Server Setup', slug: 'guides/headless' },
            { label: 'Parquet Analytics', slug: 'guides/parquet' },
            { label: 'Verify Integrity', slug: 'guides/verification' },
          ],
        },
        {
          label: 'Architecture',
          items: [
            { label: 'Overview', slug: 'architecture/overview' },
            { label: 'Database Schema', slug: 'architecture/schema' },
            { label: 'Data Storage', slug: 'architecture/storage' },
          ],
        },
        { label: 'Troubleshooting', slug: 'troubleshooting' },
        { label: 'Development', slug: 'development' },
      ],
    }),
  ],
});
