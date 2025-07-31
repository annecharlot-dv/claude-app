const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Performance analysis script for build optimization
class PerformanceAnalyzer {
  constructor() {
    this.buildDir = path.join(__dirname, '../build');
    this.reportDir = path.join(__dirname, '../performance-reports');
    this.thresholds = {
      maxBundleSize: 512 * 1024, // 512KB
      maxChunkSize: 256 * 1024,  // 256KB
      maxAssetSize: 100 * 1024,  // 100KB
    };
  }

  async analyzeBuild() {
    console.log('🔍 Analyzing build performance...');
    
    if (!fs.existsSync(this.reportDir)) {
      fs.mkdirSync(this.reportDir, { recursive: true });
    }

    const analysis = {
      timestamp: new Date().toISOString(),
      bundleAnalysis: this.analyzeBundleSize(),
      assetAnalysis: this.analyzeAssets(),
      recommendations: [],
      passed: true
    };

    // Generate recommendations
    this.generateRecommendations(analysis);
    
    // Save report
    const reportPath = path.join(this.reportDir, `build-analysis-${Date.now()}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(analysis, null, 2));
    
    console.log(`📊 Performance report saved to: ${reportPath}`);
    
    // Exit with error if thresholds exceeded
    if (!analysis.passed) {
      console.error('❌ Build performance thresholds exceeded!');
      process.exit(1);
    }
    
    console.log('✅ Build performance analysis passed!');
    return analysis;
  }

  analyzeBundleSize() {
    const staticDir = path.join(this.buildDir, 'static');
    const jsDir = path.join(staticDir, 'js');
    const cssDir = path.join(staticDir, 'css');
    
    const analysis = {
      totalSize: 0,
      jsFiles: [],
      cssFiles: [],
      largestFiles: []
    };

    // Analyze JS files
    if (fs.existsSync(jsDir)) {
      const jsFiles = fs.readdirSync(jsDir);
      jsFiles.forEach(file => {
        const filePath = path.join(jsDir, file);
        const stats = fs.statSync(filePath);
        const fileInfo = {
          name: file,
          size: stats.size,
          sizeKB: Math.round(stats.size / 1024),
          type: 'js'
        };
        analysis.jsFiles.push(fileInfo);
        analysis.totalSize += stats.size;
      });
    }

    // Analyze CSS files
    if (fs.existsSync(cssDir)) {
      const cssFiles = fs.readdirSync(cssDir);
      cssFiles.forEach(file => {
        const filePath = path.join(cssDir, file);
        const stats = fs.statSync(filePath);
        const fileInfo = {
          name: file,
          size: stats.size,
          sizeKB: Math.round(stats.size / 1024),
          type: 'css'
        };
        analysis.cssFiles.push(fileInfo);
        analysis.totalSize += stats.size;
      });
    }

    // Find largest files
    const allFiles = [...analysis.jsFiles, ...analysis.cssFiles];
    analysis.largestFiles = allFiles
      .sort((a, b) => b.size - a.size)
      .slice(0, 10);

    return analysis;
  }

  analyzeAssets() {
    const staticDir = path.join(this.buildDir, 'static');
    const mediaDir = path.join(staticDir, 'media');
    
    const analysis = {
      totalAssets: 0,
      totalSize: 0,
      imageFiles: [],
      otherFiles: []
    };

    if (fs.existsSync(mediaDir)) {
      const files = fs.readdirSync(mediaDir);
      files.forEach(file => {
        const filePath = path.join(mediaDir, file);
        const stats = fs.statSync(filePath);
        const fileInfo = {
          name: file,
          size: stats.size,
          sizeKB: Math.round(stats.size / 1024)
        };

        analysis.totalAssets++;
        analysis.totalSize += stats.size;

        if (file.match(/\.(jpg|jpeg|png|gif|svg|webp)$/i)) {
          analysis.imageFiles.push(fileInfo);
        } else {
          analysis.otherFiles.push(fileInfo);
        }
      });
    }

    return analysis;
  }

  generateRecommendations(analysis) {
    const { bundleAnalysis, assetAnalysis } = analysis;
    
    // Check bundle size thresholds
    const mainBundle = bundleAnalysis.jsFiles.find(f => f.name.includes('main'));
    if (mainBundle && mainBundle.size > this.thresholds.maxBundleSize) {
      analysis.recommendations.push({
        type: 'bundle-size',
        severity: 'high',
        message: `Main bundle size (${mainBundle.sizeKB}KB) exceeds threshold (${this.thresholds.maxBundleSize / 1024}KB)`,
        suggestions: [
          'Implement code splitting with React.lazy()',
          'Use dynamic imports for large dependencies',
          'Consider removing unused dependencies',
          'Enable tree shaking optimization'
        ]
      });
      analysis.passed = false;
    }

    // Check for large chunks
    bundleAnalysis.jsFiles.forEach(file => {
      if (file.size > this.thresholds.maxChunkSize) {
        analysis.recommendations.push({
          type: 'chunk-size',
          severity: 'medium',
          message: `Chunk ${file.name} (${file.sizeKB}KB) is larger than recommended`,
          suggestions: [
            'Split large components into smaller chunks',
            'Use route-based code splitting',
            'Lazy load heavy dependencies'
          ]
        });
      }
    });

    // Check asset sizes
    assetAnalysis.imageFiles.forEach(file => {
      if (file.size > this.thresholds.maxAssetSize) {
        analysis.recommendations.push({
          type: 'asset-size',
          severity: 'medium',
          message: `Image ${file.name} (${file.sizeKB}KB) could be optimized`,
          suggestions: [
            'Compress images using tools like imagemin',
            'Convert to WebP format for better compression',
            'Use responsive images with srcset',
            'Consider lazy loading for below-the-fold images'
          ]
        });
      }
    });

    // Check total bundle size
    const totalBundleSize = bundleAnalysis.totalSize;
    if (totalBundleSize > this.thresholds.maxBundleSize * 2) {
      analysis.recommendations.push({
        type: 'total-size',
        severity: 'high',
        message: `Total bundle size (${Math.round(totalBundleSize / 1024)}KB) is too large`,
        suggestions: [
          'Implement aggressive code splitting',
          'Use a bundle analyzer to identify large dependencies',
          'Consider using a CDN for large libraries',
          'Implement progressive loading strategies'
        ]
      });
      analysis.passed = false;
    }
  }
}

// Run analysis
if (require.main === module) {
  const analyzer = new PerformanceAnalyzer();
  analyzer.analyzeBuild().catch(console.error);
}

module.exports = PerformanceAnalyzer;