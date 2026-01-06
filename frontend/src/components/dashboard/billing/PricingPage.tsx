import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { useSubscription } from '../../../hooks/useSubscription'
import { PRICING_TIERS } from '../../../types/billing'
import {
  PageContainer,
  PageTitle,
  BackLink,
  PlanCard,
  PlanName,
  PlanPrice,
  PlanPeriod,
  FeatureList,
  FeatureItem,
  UpgradeButton,
  CurrentPlanButton,
  PricingToggle,
  ToggleLabel,
  ToggleSwitch,
  SaveBadge,
  LoadingSpinner,
  ErrorMessage
} from './shared/styles'

const PageHeaderCentered = styled.div`
  text-align: center;
  margin-bottom: 2rem;
`

const Subtitle = styled.p`
  color: #6b7280;
  font-size: 1.125rem;
  margin: 0.5rem 0 0 0;
`

const PricingGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
  max-width: 800px;
  margin: 0 auto;
`

const GuaranteeSection = styled.div`
  text-align: center;
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 12px;
`

const GuaranteeTitle = styled.h3`
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
`

const GuaranteeText = styled.p`
  color: #6b7280;
  font-size: 0.9375rem;
  margin: 0;
`

const FAQSection = styled.div`
  margin-top: 3rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
`

const FAQTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  text-align: center;
  margin-bottom: 1.5rem;
`

const FAQItem = styled.details`
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 0.75rem;
  background: white;

  &[open] summary {
    border-bottom: 1px solid #e5e7eb;
  }
`

const FAQQuestion = styled.summary`
  padding: 1rem 1.25rem;
  font-weight: 600;
  color: #1f2937;
  cursor: pointer;
  list-style: none;
  display: flex;
  justify-content: space-between;
  align-items: center;

  &::-webkit-details-marker {
    display: none;
  }

  &:after {
    content: '+';
    font-size: 1.25rem;
    color: #6b7280;
  }

  details[open] &:after {
    content: '-';
  }
`

const FAQAnswer = styled.div`
  padding: 1rem 1.25rem;
  color: #6b7280;
  font-size: 0.9375rem;
  line-height: 1.6;
`

export function PricingPage() {
  const navigate = useNavigate()
  const [isYearly, setIsYearly] = useState(true)
  const {
    tier,
    isPro,
    loading,
    error,
    startCheckout,
    checkoutLoading,
    openBillingPortal,
    portalLoading
  } = useSubscription()

  const handleUpgrade = async (priceType: 'monthly' | 'yearly') => {
    try {
      await startCheckout(priceType)
    } catch {
      // Error is handled by the hook
    }
  }

  if (loading) {
    return (
      <PageContainer>
        <LoadingSpinner />
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <BackLink onClick={() => navigate('/dashboard/billing')}>
        ← Back to Billing
      </BackLink>

      <PageHeaderCentered>
        <PageTitle style={{ justifyContent: 'center' }}>
          Choose Your Plan
        </PageTitle>
        <Subtitle>
          Start free, upgrade when you need more features
        </Subtitle>
      </PageHeaderCentered>

      {error && <ErrorMessage>{error}</ErrorMessage>}

      {/* Billing Toggle */}
      <PricingToggle>
        <ToggleLabel $active={!isYearly} onClick={() => setIsYearly(false)}>
          Monthly
        </ToggleLabel>
        <ToggleSwitch
          $checked={isYearly}
          onClick={() => setIsYearly(!isYearly)}
        />
        <ToggleLabel $active={isYearly} onClick={() => setIsYearly(true)}>
          Yearly <SaveBadge>Save 17%</SaveBadge>
        </ToggleLabel>
      </PricingToggle>

      {/* Pricing Cards */}
      <PricingGrid>
        {PRICING_TIERS.map((plan) => {
          const isCurrent = tier === plan.id
          const price = isYearly ? plan.yearlyPrice : plan.monthlyPrice
          const period = isYearly ? '/year' : '/month'

          return (
            <PlanCard
              key={plan.id}
              $current={isCurrent}
              $popular={plan.isPopular}
            >
              <PlanName>{plan.name}</PlanName>
              <PlanPrice>
                ${price}
                {price > 0 && <span>{period}</span>}
              </PlanPrice>
              {plan.id === 'pro' && isYearly && (
                <PlanPeriod>
                  ${(plan.yearlyPrice / 12).toFixed(2)}/month, billed annually
                </PlanPeriod>
              )}
              {plan.id === 'free' && (
                <PlanPeriod>Free forever</PlanPeriod>
              )}

              <FeatureList>
                {plan.features.map((feature, idx) => (
                  <FeatureItem key={idx} $included={feature.included}>
                    {feature.name}
                  </FeatureItem>
                ))}
              </FeatureList>

              {isCurrent ? (
                <CurrentPlanButton>Current Plan</CurrentPlanButton>
              ) : plan.id === 'free' ? (
                isPro ? (
                  <CurrentPlanButton
                    as="button"
                    style={{ cursor: 'pointer', background: '#f3f4f6' }}
                    onClick={openBillingPortal}
                    disabled={portalLoading}
                  >
                    {portalLoading ? 'Loading...' : 'Manage Subscription'}
                  </CurrentPlanButton>
                ) : (
                  <CurrentPlanButton>Current Plan</CurrentPlanButton>
                )
              ) : (
                <UpgradeButton
                  onClick={() => handleUpgrade(isYearly ? 'yearly' : 'monthly')}
                  disabled={checkoutLoading}
                >
                  {checkoutLoading ? 'Redirecting...' : 'Upgrade to Pro'}
                </UpgradeButton>
              )}
            </PlanCard>
          )
        })}
      </PricingGrid>

      {/* Money-back guarantee */}
      <GuaranteeSection>
        <GuaranteeTitle>30-Day Money-Back Guarantee</GuaranteeTitle>
        <GuaranteeText>
          Try Pro risk-free. If you're not satisfied, get a full refund within 30 days.
        </GuaranteeText>
      </GuaranteeSection>

      {/* FAQ */}
      <FAQSection>
        <FAQTitle>Frequently Asked Questions</FAQTitle>

        <FAQItem>
          <FAQQuestion>Can I cancel anytime?</FAQQuestion>
          <FAQAnswer>
            Yes! You can cancel your subscription at any time. You'll continue to have
            access to Pro features until the end of your billing period.
          </FAQAnswer>
        </FAQItem>

        <FAQItem>
          <FAQQuestion>What payment methods do you accept?</FAQQuestion>
          <FAQAnswer>
            We accept all major credit cards (Visa, Mastercard, American Express)
            through our secure payment processor, Stripe. We also support Apple Pay
            and Google Pay.
          </FAQAnswer>
        </FAQItem>

        <FAQItem>
          <FAQQuestion>Can I switch from monthly to yearly?</FAQQuestion>
          <FAQAnswer>
            Absolutely! You can upgrade to yearly billing at any time to save 17%.
            The change will take effect at your next billing cycle.
          </FAQAnswer>
        </FAQItem>

        <FAQItem>
          <FAQQuestion>What happens if my payment fails?</FAQQuestion>
          <FAQAnswer>
            We'll notify you and retry the payment a few times. If the payment
            continues to fail, your subscription will be paused, but you won't
            lose any data.
          </FAQAnswer>
        </FAQItem>

        <FAQItem>
          <FAQQuestion>Do you offer refunds?</FAQQuestion>
          <FAQAnswer>
            Yes, we offer a 30-day money-back guarantee for new subscribers.
            Contact support if you're not satisfied with your purchase.
          </FAQAnswer>
        </FAQItem>
      </FAQSection>
    </PageContainer>
  )
}

export default PricingPage
