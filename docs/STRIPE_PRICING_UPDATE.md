# Stripe Pricing Update - Seed Files

## Summary

Updated all seed files to use **actual Stripe pricing** from your connected Stripe account (via MCP).

## Changes Made

### Previous (Fake IDs):
- ❌ `starter` plan with fake IDs (`price_starter_monthly`, `prod_starter`)
- ❌ `pro` plan with fake IDs (`price_pro_monthly`, `prod_pro`)
- ❌ `business` plan with fake IDs (`price_business_monthly`, `prod_business`)

### Updated (Real Stripe IDs):

#### 1. **Basic Plan** (formerly "Starter")
- **Product ID**: `prod_SmwOSjZOdHh8R2`
- **Monthly Price ID**: `price_1Rsk6eD9jtDTgtt7wOVii0Uv` ($28.00/month)
- **Yearly Price ID**: `price_1Rsk6fD9jtDTgtt7atHuhVi0` ($199.00/year)
- **Features**: 3 projects, 5 team members, 5GB storage, Basic support

#### 2. **Premium Subscription** (formerly "Pro")
- **Product ID**: `prod_SmwOCZUzUTQ5Zi`
- **Monthly Price ID**: `price_1Rsk6gD9jtDTgtt7D6J4QE4k` ($68.00/month)
- **Yearly Price ID**: `price_1Rsk6gD9jtDTgtt7KbZqwLhV` ($450.00/year)
- **Features**: 10 projects, 20 team members, 50GB storage, Priority support, Advanced analytics

#### 3. **Enterprise Solution** (formerly "Business")
- **Product ID**: `prod_SmwOdGQRNlyp3D`
- **Monthly Price ID**: `price_1Rsk6bD9jtDTgtt7YVFraetI` ($255.00/month)
- **Yearly Price ID**: `price_1Rsk6dD9jtDTgtt7qEkMYgBF` ($1,999.00/year)
- **Features**: Unlimited projects, 100 team members, 500GB storage, 24/7 priority support, Advanced analytics, Custom integrations, Dedicated account manager

## Files Updated

1. ✅ `scripts/seed/subscription_plans.py` - Plan definitions with real Stripe IDs
2. ✅ `scripts/seed.py` - Main seed script with subscription assignments
3. ✅ `scripts/seed/subscriptions.py` - Subscription and billing history

## Organization Subscription Assignments

The seed data now assigns:
- **Development Team**: Enterprise Solution ($255/month)
- **Marketing Team**: Premium Subscription ($68/month)
- **Research Team**: Basic Plan ($28/month)
- **Sales Department**: Premium Subscription (trialing)
- **Customer Success**: Free Plan

## Additional Stripe Products Available

Your Stripe account also has these one-time payment products (not used in seed):
- API Access ($80 one-time)
- Team Collaboration ($120 one-time)
- Pro Analytics ($150 one-time)
- Professional Services ($250 one-time)
- Starter Kit ($49 one-time)
- Basic Analytics ($5 one-time)
- Advanced Reporting ($50 one-time)
- White Label Solution ($150 one-time)

## Next Steps

1. **Run the seed script** to populate your database with the updated pricing:
   ```bash
   cd backend
   python scripts/seed.py
   ```

2. **Or run fresh seed** (deletes all data first):
   ```bash
   python scripts/seed_fresh.py
   ```

3. **Verify in your application** that the pricing displays correctly and matches your Stripe dashboard.

## Notes

- All prices are stored in cents (e.g., $28.00 = 2800 cents)
- Pricing includes USD, EUR, GBP, and BRL currencies
- The Free plan has no Stripe IDs (as it's free and doesn't require Stripe integration)
- All subscription plans are marked as active and ready to use

## Verification

You can verify the pricing in Stripe Dashboard:
- Test Mode Dashboard: https://dashboard.stripe.com/test/products
- Compare the product/price IDs with those in the seed files

