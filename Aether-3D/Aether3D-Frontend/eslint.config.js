import js from '@eslint/js';
import reactPlugin from 'eslint-plugin-react';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx}'],
    ...reactPlugin.configs.flat.recommended,
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.es2021,
        ...globals.node,
      },
    },
    rules: {
      'react/react-in-jsx-scope': 'off',
      'no-unused-vars': ['warn', { vars: 'all', args: 'after-used' }],
      'react/prop-types': 'off',
    },
  },
  {
    ignores: ['dist/', 'node_modules/', 'public/'],
  },
];
