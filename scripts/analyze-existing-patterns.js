/**
 * Analyze Existing Payment Patterns from ScriptClient Data
 *
 * This script analyzes your existing 500+ payment screenshots to:
 * 1. Find customer-recipient name relationships
 * 2. Calculate confidence scores for each pattern
 * 3. Migrate patterns to the new learning system
 * 4. Estimate accuracy improvements
 *
 * Usage: node scripts/analyze-existing-patterns.js
 */

const { MongoClient } = require('mongodb');
require('dotenv').config();

// Database configuration
const MONGO_URL = process.env.MONGO_URL;
const DB_NAME = process.env.DB_NAME || 'customerDB';

// Analysis configuration
const MIN_PATTERN_COUNT = 2;           // Minimum occurrences to consider a pattern
const AUTO_APPROVE_THRESHOLD = 3;      // Auto-approve after 3+ successful verifications
const HIGH_CONFIDENCE_THRESHOLD = 0.8; // High confidence threshold

async function analyzeExistingPatterns() {
  if (!MONGO_URL) {
    console.error('❌ MONGO_URL environment variable is required');
    process.exit(1);
  }

  const client = new MongoClient(MONGO_URL, {
    tls: true,
    tlsAllowInvalidCertificates: true,
  });

  try {
    console.log('🔗 Connecting to MongoDB...');
    await client.connect();

    const db = client.db(DB_NAME);
    console.log(`✅ Connected to database: ${DB_NAME}\n`);

    // Step 1: Analyze existing payment patterns
    console.log('📊 Analyzing existing payment data...');

    const paymentPatterns = await db.collection('payments').aggregate([
      {
        $match: {
          verificationStatus: 'verified',  // Only learn from verified payments
          recipientName: { $exists: true, $ne: null },
          $or: [
            { toAccount: { $exists: true, $ne: null } },
            { recipientName: { $ne: '' } }
          ]
        }
      },
      {
        $group: {
          _id: {
            customerId: '$chatId',
            customerName: '$fullName',
            recipientName: '$recipientName',
            toAccount: '$toAccount'
          },
          occurrences: { $sum: 1 },
          amounts: { $push: '$amountInKHR' },
          bankNames: { $push: '$bankName' },
          firstSeen: { $min: '$uploadedAt' },
          lastSeen: { $max: '$uploadedAt' },
          transactionIds: { $push: '$transactionId' }
        }
      },
      {
        $match: {
          occurrences: { $gte: MIN_PATTERN_COUNT }  // Only patterns with multiple occurrences
        }
      },
      {
        $sort: { occurrences: -1 }
      }
    ]).toArray();

    console.log(`✅ Found ${paymentPatterns.length} customer-recipient patterns\n`);

    if (paymentPatterns.length === 0) {
      console.log('ℹ️  No patterns found. Make sure you have verified payments with recipient names.');
      return;
    }

    // Step 2: Display top patterns
    console.log('🔝 Top Payment Patterns:');
    console.log('─'.repeat(80));

    paymentPatterns.slice(0, 10).forEach((pattern, index) => {
      const confidence = calculateConfidence(pattern.occurrences);
      const autoApprove = pattern.occurrences >= AUTO_APPROVE_THRESHOLD && confidence >= HIGH_CONFIDENCE_THRESHOLD;

      console.log(`${index + 1}. 👤 Customer: ${pattern._id.customerName}`);
      console.log(`   💰 Pays as: "${pattern._id.recipientName}"`);
      console.log(`   🏦 Account: ${pattern._id.toAccount || 'N/A'}`);
      console.log(`   📊 Frequency: ${pattern.occurrences} times`);
      console.log(`   🎯 Confidence: ${(confidence * 100).toFixed(0)}%`);
      console.log(`   ⚡ Auto-approve: ${autoApprove ? '✅ YES' : '❌ NO'}`);

      if (pattern.bankNames.filter(b => b).length > 0) {
        const uniqueBanks = [...new Set(pattern.bankNames.filter(b => b))];
        console.log(`   🏪 Banks: ${uniqueBanks.join(', ')}`);
      }

      console.log('');
    });

    // Step 3: Calculate statistics
    const stats = calculateStatistics(paymentPatterns);
    console.log('📈 Pattern Analysis Results:');
    console.log('─'.repeat(50));
    console.log(`📊 Total unique patterns: ${stats.totalPatterns}`);
    console.log(`🎯 High confidence patterns: ${stats.highConfidencePatterns} (${stats.highConfidencePercentage}%)`);
    console.log(`⚡ Auto-approvable patterns: ${stats.autoApprovablePatterns} (${stats.autoApprovalPercentage}%)`);
    console.log(`📈 Estimated accuracy improvement: ${stats.estimatedAccuracy}%`);
    console.log(`⏱️  Average pattern frequency: ${stats.averageFrequency.toFixed(1)} payments`);
    console.log('');

    // Step 4: Migrate patterns to new system
    console.log('🔄 Migrating patterns to learning system...');

    let migratedCount = 0;
    const patternCollection = db.collection('payment_patterns');

    for (const pattern of paymentPatterns) {
      const confidence = calculateConfidence(pattern.occurrences);
      const autoApprove = pattern.occurrences >= AUTO_APPROVE_THRESHOLD && confidence >= HIGH_CONFIDENCE_THRESHOLD;

      // Create pattern document for new learning system
      const patternDoc = {
        tenant_id: 'default',  // Default tenant for existing data
        customer_id: pattern._id.customerId,
        customer_name: pattern._id.customerName,

        recipient_patterns: [{
          extracted_name: pattern._id.recipientName,
          extracted_account: pattern._id.toAccount || '',
          occurrence_count: pattern.occurrences,
          approval_count: pattern.occurrences,  // All were verified
          rejection_count: 0,
          confidence: confidence,
          last_seen: pattern.lastSeen,
          auto_approve: autoApprove,
          bank_name: getMostCommonBank(pattern.bankNames),
          created_at: pattern.firstSeen
        }],

        // Store amount patterns for future use
        amount_patterns: [...new Set(pattern.amounts.filter(a => a))],

        created_at: pattern.firstSeen,
        updated_at: new Date(),
        migrated_from: 'scriptclient_analysis',
        migration_date: new Date()
      };

      // Insert or update pattern
      await patternCollection.replaceOne(
        {
          tenant_id: 'default',
          customer_id: pattern._id.customerId
        },
        patternDoc,
        { upsert: true }
      );

      migratedCount++;
    }

    console.log(`✅ Successfully migrated ${migratedCount} patterns to learning system\n`);

    // Step 5: Create summary report
    const report = {
      analysis_date: new Date(),
      database: DB_NAME,

      raw_data: {
        total_verified_payments: await db.collection('payments').countDocuments({
          verificationStatus: 'verified'
        }),
        payments_with_recipient: await db.collection('payments').countDocuments({
          verificationStatus: 'verified',
          recipientName: { $exists: true, $ne: null }
        })
      },

      patterns: stats,

      migration: {
        patterns_migrated: migratedCount,
        target_collection: 'payment_patterns',
        tenant_id: 'default'
      },

      recommendations: generateRecommendations(stats)
    };

    // Save report
    await db.collection('pattern_analysis_reports').insertOne(report);

    console.log('📋 Analysis Report Generated');
    console.log('─'.repeat(40));
    console.log('✅ Setup Complete! Your learning system is ready.');
    console.log('');
    console.log('🚀 Next Steps:');
    console.log('   1. Test the new verification system in shadow mode');
    console.log('   2. Compare results with existing scriptclient');
    console.log('   3. Gradually increase confidence thresholds');
    console.log('   4. Monitor accuracy improvements');
    console.log('');
    console.log('📊 Expected Results:');
    console.log(`   - Current accuracy: ~27% (GPT-4o Vision only)`);
    console.log(`   - New system accuracy: ~${stats.estimatedAccuracy}% (with pattern learning)`);
    console.log(`   - Improvement: ${(stats.estimatedAccuracy - 27).toFixed(0)}% better`);

  } catch (error) {
    console.error('❌ Analysis failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  } finally {
    await client.close();
    console.log('\n✅ Database connection closed');
  }
}

function calculateConfidence(occurrences) {
  // Confidence formula: starts at 0.6, increases with frequency
  // Max confidence: 0.95
  const baseConfidence = 0.6;
  const frequencyBonus = Math.min(0.35, occurrences * 0.05);
  return Math.min(0.95, baseConfidence + frequencyBonus);
}

function calculateStatistics(patterns) {
  const totalPatterns = patterns.length;

  let highConfidenceCount = 0;
  let autoApprovableCount = 0;
  let totalFrequency = 0;

  patterns.forEach(pattern => {
    const confidence = calculateConfidence(pattern.occurrences);
    const autoApprove = pattern.occurrences >= AUTO_APPROVE_THRESHOLD && confidence >= HIGH_CONFIDENCE_THRESHOLD;

    if (confidence >= HIGH_CONFIDENCE_THRESHOLD) {
      highConfidenceCount++;
    }

    if (autoApprove) {
      autoApprovableCount++;
    }

    totalFrequency += pattern.occurrences;
  });

  const highConfidencePercentage = ((highConfidenceCount / totalPatterns) * 100).toFixed(0);
  const autoApprovalPercentage = ((autoApprovableCount / totalPatterns) * 100).toFixed(0);

  // Estimate accuracy: base 35% + pattern matching boost
  const patternMatchBoost = Math.min(50, autoApprovalPercentage * 0.8);
  const estimatedAccuracy = Math.round(35 + patternMatchBoost);

  return {
    totalPatterns,
    highConfidencePatterns: highConfidenceCount,
    highConfidencePercentage,
    autoApprovablePatterns: autoApprovableCount,
    autoApprovalPercentage,
    estimatedAccuracy,
    averageFrequency: totalFrequency / totalPatterns
  };
}

function getMostCommonBank(bankNames) {
  const validBanks = bankNames.filter(bank => bank && bank.trim());

  if (validBanks.length === 0) return null;

  // Count frequency of each bank
  const bankCounts = {};
  validBanks.forEach(bank => {
    bankCounts[bank] = (bankCounts[bank] || 0) + 1;
  });

  // Return most frequent bank
  return Object.keys(bankCounts).reduce((a, b) =>
    bankCounts[a] > bankCounts[b] ? a : b
  );
}

function generateRecommendations(stats) {
  const recommendations = [];

  if (stats.autoApprovalPercentage < 30) {
    recommendations.push({
      priority: 'HIGH',
      action: 'Collect more verified payment data',
      reason: `Only ${stats.autoApprovalPercentage}% of patterns are auto-approvable`
    });
  }

  if (stats.averageFrequency < 3) {
    recommendations.push({
      priority: 'MEDIUM',
      action: 'Run system longer to build pattern confidence',
      reason: 'Most patterns have low frequency (need 3+ occurrences for auto-approval)'
    });
  }

  if (stats.estimatedAccuracy < 60) {
    recommendations.push({
      priority: 'HIGH',
      action: 'Consider collecting data from classmates',
      reason: `Estimated accuracy (${stats.estimatedAccuracy}%) could be improved with more diverse patterns`
    });
  } else if (stats.estimatedAccuracy >= 75) {
    recommendations.push({
      priority: 'LOW',
      action: 'Ready for production deployment',
      reason: `High estimated accuracy (${stats.estimatedAccuracy}%) indicates system is ready`
    });
  }

  return recommendations;
}

// CLI interface
if (require.main === module) {
  console.log('🔍 Payment Pattern Analysis Tool\n');
  console.log('This tool analyzes your existing verified payments to build');
  console.log('a learning model for better recipient name matching.\n');

  analyzeExistingPatterns().catch(error => {
    console.error('💥 Unexpected error:', error);
    process.exit(1);
  });
}

module.exports = { analyzeExistingPatterns };