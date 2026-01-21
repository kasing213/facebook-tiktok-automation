/**
 * Setup script for Pattern Learning Database Collections
 *
 * This script creates MongoDB collections for the learning system
 * Works with existing scriptclient and ocr-service databases
 *
 * Usage: node scripts/setup-pattern-learning-db.js
 */

const { MongoClient } = require('mongodb');
require('dotenv').config();

// Database configuration
const MONGO_URL = process.env.MONGO_URL;
const DB_NAME = process.env.DB_NAME || 'customerDB';

async function setupPatternLearningDB() {
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

    // 1. Create payment_patterns collection for learning customer behaviors
    console.log('📊 Creating payment_patterns collection...');
    const paymentPatternsExists = await db.listCollections({name: 'payment_patterns'}).hasNext();

    if (!paymentPatternsExists) {
      await db.createCollection('payment_patterns');
      console.log('✅ Created payment_patterns collection');
    } else {
      console.log('ℹ️  payment_patterns collection already exists');
    }

    // Create indexes for payment_patterns
    await db.collection('payment_patterns').createIndex({ customer_id: 1 }, { unique: true });
    await db.collection('payment_patterns').createIndex({ tenant_id: 1, customer_id: 1 });
    await db.collection('payment_patterns').createIndex({ 'recipient_patterns.extracted_name': 1 });
    await db.collection('payment_patterns').createIndex({ updated_at: -1 });
    console.log('✅ Created indexes for payment_patterns');

    // 2. Create merchant_recipients collection for valid recipient configurations
    console.log('\n🏪 Creating merchant_recipients collection...');
    const merchantRecipientsExists = await db.listCollections({name: 'merchant_recipients'}).hasNext();

    if (!merchantRecipientsExists) {
      await db.createCollection('merchant_recipients');
      console.log('✅ Created merchant_recipients collection');
    } else {
      console.log('ℹ️  merchant_recipients collection already exists');
    }

    // Create indexes for merchant_recipients
    await db.collection('merchant_recipients').createIndex({ tenant_id: 1, merchant_id: 1 }, { unique: true });
    await db.collection('merchant_recipients').createIndex({ tenant_id: 1 });
    console.log('✅ Created indexes for merchant_recipients');

    // 3. Create verification_queue collection for manual review
    console.log('\n📋 Creating verification_queue collection...');
    const verificationQueueExists = await db.listCollections({name: 'verification_queue'}).hasNext();

    if (!verificationQueueExists) {
      await db.createCollection('verification_queue');
      console.log('✅ Created verification_queue collection');
    } else {
      console.log('ℹ️  verification_queue collection already exists');
    }

    // Create indexes for verification_queue
    await db.collection('verification_queue').createIndex({ tenant_id: 1, status: 1 });
    await db.collection('verification_queue').createIndex({ invoice_id: 1 });
    await db.collection('verification_queue').createIndex({ screenshot_id: 1 });
    await db.collection('verification_queue').createIndex({ created_at: -1 });
    console.log('✅ Created indexes for verification_queue');

    // 4. Create shadow_mode_results for A/B testing
    console.log('\n🔬 Creating shadow_mode_results collection...');
    const shadowModeExists = await db.listCollections({name: 'shadow_mode_results'}).hasNext();

    if (!shadowModeExists) {
      await db.createCollection('shadow_mode_results');
      console.log('✅ Created shadow_mode_results collection');
    } else {
      console.log('ℹ️  shadow_mode_results collection already exists');
    }

    // Create indexes for shadow_mode_results
    await db.collection('shadow_mode_results').createIndex({ timestamp: -1 });
    await db.collection('shadow_mode_results').createIndex({ tenant_id: 1, timestamp: -1 });
    console.log('✅ Created indexes for shadow_mode_results');

    // 5. Create initial merchant recipient config (your default setup)
    console.log('\n🏗️  Creating default merchant recipient configuration...');
    const defaultMerchantConfig = {
      tenant_id: 'default',
      merchant_id: 'ks_automation',

      // Your current hardcoded recipients (migrated from botfetch.js)
      valid_recipients: [
        {
          type: 'primary',
          bank_name: 'ABA Bank',
          account_numbers: ['086228226', '086 228 226'],
          account_names: ['CHAN KASING', 'CHAN K.', 'Chan Kasing', 'K. CHAN'],
          khqr_names: ['CHAN K. & THOEURN T.', 'CHAN K']
        },
        {
          type: 'partner',
          bank_name: 'ABA Bank',
          account_numbers: [],
          account_names: ['THOEURN THEARY', 'THOEURN T.', 'T. THOEURN']
        }
      ],

      // Configuration
      allow_any_recipient: false,  // Strict recipient checking
      strict_mode: false,          // Allow fuzzy matching
      confidence_threshold: 0.75,  // Auto-approve threshold

      // Metadata
      created_at: new Date(),
      updated_at: new Date(),
      created_by: 'setup_script'
    };

    const existingConfig = await db.collection('merchant_recipients').findOne({
      tenant_id: 'default',
      merchant_id: 'ks_automation'
    });

    if (!existingConfig) {
      await db.collection('merchant_recipients').insertOne(defaultMerchantConfig);
      console.log('✅ Created default merchant recipient configuration');
      console.log('   - Account: 086228226 (CHAN KASING)');
      console.log('   - Variations: CHAN K., K. CHAN, THOEURN T.');
      console.log('   - Fuzzy matching enabled');
    } else {
      console.log('ℹ️  Default merchant configuration already exists');
    }

    // 6. Show statistics about existing data
    console.log('\n📊 Analyzing existing data...');

    const paymentsCollection = db.collection('payments');
    const totalPayments = await paymentsCollection.countDocuments();
    const verifiedPayments = await paymentsCollection.countDocuments({
      verificationStatus: 'verified'
    });
    const paymentsWithRecipient = await paymentsCollection.countDocuments({
      recipientName: { $exists: true, $ne: null }
    });

    console.log(`   - Total payments: ${totalPayments}`);
    console.log(`   - Verified payments: ${verifiedPayments}`);
    console.log(`   - Payments with recipient name: ${paymentsWithRecipient}`);

    if (verifiedPayments > 0) {
      console.log(`   - Ready for pattern learning: ${verifiedPayments} samples ✅`);

      if (verifiedPayments >= 100) {
        console.log('   - Sufficient data for training (100+ samples) 🎯');
      } else if (verifiedPayments >= 50) {
        console.log('   - Good data for initial training (50+ samples) 👍');
      } else {
        console.log('   - Limited data, but training possible (need more samples) ⚠️');
      }
    } else {
      console.log('   - No verified payments found - run system to collect data first');
    }

    console.log('\n🎉 Pattern Learning Database Setup Complete!');
    console.log('\n📋 Next steps:');
    console.log('   1. Run: node scripts/analyze-existing-patterns.js');
    console.log('   2. Train the model on your existing verified payments');
    console.log('   3. Test in shadow mode before switching');
    console.log('   4. Monitor accuracy improvements');

  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    process.exit(1);
  } finally {
    await client.close();
    console.log('\n✅ Database connection closed');
  }
}

// CLI interface
if (require.main === module) {
  console.log('🚀 Pattern Learning Database Setup\n');
  setupPatternLearningDB();
}

module.exports = { setupPatternLearningDB };