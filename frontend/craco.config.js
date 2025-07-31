// Performance-optimized CRACO configuration
const path = require('path');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

// Environment variable overrides
const config = {
  disableHotReload: process.env.DISABLE_HOT_RELOAD === 'true',
  analyzeBundles: process.env.ANALYZE_BUNDLES === 'true',
};

module.exports = {
  webpack: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
    configure: (webpackConfig, { env }) => {
      
      // Production optimizations
      if (env === 'production') {
        // Enable advanced optimizations
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          splitChunks: {
            chunks: 'all',
            cacheGroups: {
              vendor: {
                test: /[\\/]node_modules[\\/]/,
                name: 'vendors',
                chunks: 'all',
                priority: 10,
              },
              react: {
                test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
                name: 'react',
                chunks: 'all',
                priority: 20,
              },
              common: {
                name: 'common',
                minChunks: 2,
                chunks: 'all',
                priority: 5,
                reuseExistingChunk: true,
              },
            },
          },
          runtimeChunk: 'single',
          moduleIds: 'deterministic',
          chunkIds: 'deterministic',
        };

        // Add bundle analyzer if requested
        if (config.analyzeBundles) {
          webpackConfig.plugins.push(
            new BundleAnalyzerPlugin({
              analyzerMode: 'static',
              openAnalyzer: false,
              reportFilename: 'bundle-report.html',
            })
          );
        }
      }
      
      // Disable hot reload completely if environment variable is set
      if (config.disableHotReload) {
        // Remove hot reload related plugins
        webpackConfig.plugins = webpackConfig.plugins.filter(plugin => {
          return !(plugin.constructor.name === 'HotModuleReplacementPlugin');
        });
        
        // Disable watch mode
        webpackConfig.watch = false;
        webpackConfig.watchOptions = {
          ignored: /.*/, // Ignore all files
        };
      } else {
        // Add ignored patterns to reduce watched directories
        webpackConfig.watchOptions = {
          ...webpackConfig.watchOptions,
          ignored: [
            '**/node_modules/**',
            '**/.git/**',
            '**/build/**',
            '**/dist/**',
            '**/coverage/**',
            '**/public/**',
          ],
        };
      }

      // Performance optimizations for all environments
      webpackConfig.resolve = {
        ...webpackConfig.resolve,
        // Reduce module resolution time
        modules: [path.resolve(__dirname, 'src'), 'node_modules'],
        // Cache module resolution
        cacheWithContext: false,
      };

      // Add performance hints
      webpackConfig.performance = {
        maxAssetSize: 512000, // 500kb
        maxEntrypointSize: 512000, // 500kb
        hints: env === 'production' ? 'warning' : false,
      };
      
      return webpackConfig;
    },
  },
  devServer: {
    // Development server optimizations
    compress: true,
    hot: !config.disableHotReload,
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
    },
  },
};