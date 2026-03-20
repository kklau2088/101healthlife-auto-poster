"""
SEO Article Topics Database for 101healthlife.com
==================================================
A rotating bank of 90+ SEO-optimised topics across all site categories.
The scheduler cycles through these automatically.
"""

TOPIC_BANK = [

    # ── Diet ─────────────────────────────────────────────────────────────────
    {"title": "7-Day Anti-Inflammatory Diet Plan for Beginners",
     "category": "Diet", "focus_keyword": "anti-inflammatory diet",
     "meta_desc": "Discover a simple 7-day anti-inflammatory diet plan to reduce chronic inflammation, boost energy, and improve overall health."},

    {"title": "The Complete Guide to the Mediterranean Diet: Benefits, Foods & Meal Plan",
     "category": "Diet", "focus_keyword": "Mediterranean diet",
     "meta_desc": "Explore the science-backed Mediterranean diet, its proven health benefits, recommended foods, and a sample weekly meal plan."},

    {"title": "Low-Carb vs. Low-Fat Diet: Which Is Better for Weight Loss?",
     "category": "Diet", "focus_keyword": "low-carb vs low-fat diet",
     "meta_desc": "A data-driven comparison of low-carb and low-fat diets to help you choose the right approach for sustainable weight loss."},

    {"title": "Intermittent Fasting: A Complete Beginner's Guide",
     "category": "Diet", "focus_keyword": "intermittent fasting guide",
     "meta_desc": "Learn everything about intermittent fasting—how it works, different methods, benefits, and tips for getting started safely."},

    {"title": "How to Eat Healthy on a Budget: 15 Practical Tips",
     "category": "Diet", "focus_keyword": "healthy eating on a budget",
     "meta_desc": "Eating nutritiously doesn't have to break the bank. Here are 15 expert-approved strategies for healthy eating on a tight budget."},

    {"title": "The Gut-Healthy Diet: Foods That Feed Your Microbiome",
     "category": "Diet", "focus_keyword": "gut healthy diet",
     "meta_desc": "Discover the best foods for a thriving gut microbiome and how a gut-healthy diet can transform your digestion, immunity, and mood."},

    {"title": "Plant-Based Diet for Beginners: What to Eat and What to Avoid",
     "category": "Diet", "focus_keyword": "plant-based diet beginners",
     "meta_desc": "Ready to go plant-based? This beginner's guide covers what to eat, nutritional pitfalls to avoid, and easy meal ideas."},

    # ── Weight Loss ──────────────────────────────────────────────────────────
    {"title": "10 Science-Backed Strategies for Sustainable Weight Loss",
     "category": "Weight Loss", "focus_keyword": "sustainable weight loss",
     "meta_desc": "Forget crash diets. Here are 10 evidence-based strategies for losing weight sustainably and keeping it off for good."},

    {"title": "How to Boost Your Metabolism Naturally: 12 Proven Methods",
     "category": "Weight Loss", "focus_keyword": "boost metabolism naturally",
     "meta_desc": "Explore 12 natural, science-backed ways to speed up your metabolism and support long-term weight management."},

    {"title": "Understanding Calorie Deficit: The Key to Effective Weight Loss",
     "category": "Weight Loss", "focus_keyword": "calorie deficit weight loss",
     "meta_desc": "Learn what a calorie deficit is, how to calculate yours, and why it's the foundation of every successful weight-loss plan."},

    {"title": "Weight Loss Plateau: Why It Happens and How to Break Through",
     "category": "Weight Loss", "focus_keyword": "weight loss plateau",
     "meta_desc": "Hit a weight-loss plateau? Discover the science behind why progress stalls and seven proven strategies to push past it."},

    {"title": "The Best Exercises for Weight Loss, Ranked by Effectiveness",
     "category": "Weight Loss", "focus_keyword": "best exercises for weight loss",
     "meta_desc": "From HIIT to strength training, we rank the most effective workouts for burning fat and achieving lasting weight loss."},

    {"title": "Ozempic for Weight Loss: Benefits, Risks, and What to Expect",
     "category": "Weight Loss", "focus_keyword": "Ozempic weight loss",
     "meta_desc": "Everything you need to know about Ozempic (semaglutide) for weight loss—how it works, side effects, and real-world results."},

    {"title": "How Sleep Affects Weight Loss: The Connection You Can't Ignore",
     "category": "Weight Loss", "focus_keyword": "sleep and weight loss",
     "meta_desc": "Poor sleep could be sabotaging your weight-loss goals. Learn how sleep quality impacts hormones, cravings, and fat burning."},

    # ── Nutrition ────────────────────────────────────────────────────────────
    {"title": "Complete Guide to Vitamins and Minerals: What You Actually Need",
     "category": "Nutrition", "focus_keyword": "vitamins and minerals guide",
     "meta_desc": "A comprehensive overview of essential vitamins and minerals, their functions, food sources, and recommended daily amounts."},

    {"title": "Protein 101: How Much Do You Really Need Each Day?",
     "category": "Nutrition", "focus_keyword": "how much protein per day",
     "meta_desc": "Find out exactly how much protein your body needs daily, the best sources, and how to optimise intake for muscle and health."},

    {"title": "The Truth About Sugar: How Much Is Too Much?",
     "category": "Nutrition", "focus_keyword": "how much sugar per day",
     "meta_desc": "Uncover the real health effects of sugar overconsumption and learn practical strategies for cutting hidden sugars from your diet."},

    {"title": "Omega-3 Fatty Acids: Benefits, Sources, and Dosage",
     "category": "Nutrition", "focus_keyword": "omega-3 fatty acids benefits",
     "meta_desc": "Explore the extensive health benefits of omega-3 fatty acids, the best dietary sources, and recommended supplementation doses."},

    {"title": "Magnesium: The Overlooked Mineral Your Body Desperately Needs",
     "category": "Nutrition", "focus_keyword": "magnesium benefits health",
     "meta_desc": "Discover why magnesium is essential for 300+ bodily functions, signs of deficiency, and the best food and supplement sources."},

    {"title": "Vitamin D Deficiency: Symptoms, Causes, and How to Fix It",
     "category": "Nutrition", "focus_keyword": "vitamin D deficiency",
     "meta_desc": "Vitamin D deficiency affects over 1 billion people worldwide. Learn the warning signs, risks, and evidence-based solutions."},

    {"title": "Probiotics vs. Prebiotics: What's the Difference and Do You Need Both?",
     "category": "Nutrition", "focus_keyword": "probiotics vs prebiotics",
     "meta_desc": "Probiotics and prebiotics both support gut health, but in different ways. Here's what the science says and how to get enough of each."},

    # ── Mental Health ────────────────────────────────────────────────────────
    {"title": "10 Proven Strategies to Manage Anxiety Naturally",
     "category": "Mental Health", "focus_keyword": "manage anxiety naturally",
     "meta_desc": "Discover 10 evidence-based, drug-free strategies to reduce anxiety and reclaim your calm—starting today."},

    {"title": "Understanding Depression: Causes, Symptoms, and Treatment Options",
     "category": "Mental Health", "focus_keyword": "understanding depression",
     "meta_desc": "A compassionate, comprehensive guide to depression: what causes it, how to recognise the signs, and the most effective treatments available."},

    {"title": "Mindfulness Meditation for Stress Relief: A Step-by-Step Guide",
     "category": "Mental Health", "focus_keyword": "mindfulness meditation stress relief",
     "meta_desc": "Learn how mindfulness meditation reduces cortisol, rewires the brain, and provides lasting stress relief—with a beginner-friendly practice plan."},

    {"title": "How to Improve Mental Health Through Exercise",
     "category": "Mental Health", "focus_keyword": "exercise mental health benefits",
     "meta_desc": "Physical activity is one of the most powerful tools for mental wellness. Explore the science and learn how to leverage exercise for better mental health."},

    {"title": "The Connection Between Gut Health and Mental Health",
     "category": "Mental Health", "focus_keyword": "gut health mental health",
     "meta_desc": "The gut-brain axis is revolutionising psychiatry. Learn how your digestive system influences mood, anxiety, and cognitive function."},

    {"title": "Burnout: Signs, Causes, and How to Recover",
     "category": "Mental Health", "focus_keyword": "burnout recovery",
     "meta_desc": "Burnout is more than just tiredness. This guide covers the stages of burnout, warning signs, and a step-by-step recovery plan."},

    # ── Health ───────────────────────────────────────────────────────────────
    {"title": "How to Strengthen Your Immune System: 15 Evidence-Based Tips",
     "category": "Health", "focus_keyword": "strengthen immune system",
     "meta_desc": "Boost your body's natural defences with these 15 science-backed lifestyle habits, foods, and supplements for a stronger immune system."},

    {"title": "High Blood Pressure: Causes, Symptoms, and Natural Remedies",
     "category": "Health", "focus_keyword": "high blood pressure natural remedies",
     "meta_desc": "Learn what causes hypertension, how to recognise it, and the most effective natural lifestyle strategies to lower your blood pressure."},

    {"title": "Type 2 Diabetes Prevention: 10 Lifestyle Changes That Work",
     "category": "Health", "focus_keyword": "type 2 diabetes prevention",
     "meta_desc": "Prevent type 2 diabetes with these 10 doctor-recommended lifestyle modifications backed by clinical research."},

    {"title": "Heart Health: The 8 Best Foods for a Healthy Heart",
     "category": "Health", "focus_keyword": "best foods for heart health",
     "meta_desc": "Protect your heart with these 8 nutrient-rich foods that are proven to lower cholesterol, reduce inflammation, and support cardiovascular health."},

    {"title": "How Much Water Should You Actually Drink Each Day?",
     "category": "Health", "focus_keyword": "how much water per day",
     "meta_desc": "The '8 glasses a day' rule is a myth. Here's what the science says about optimal daily water intake based on your body and lifestyle."},

    {"title": "The Benefits of Walking 10,000 Steps a Day—And Why It Works",
     "category": "Health", "focus_keyword": "10000 steps benefits",
     "meta_desc": "Is 10,000 steps a day the magic number? We break down the research on walking targets and their real impact on health."},

    {"title": "Understanding Inflammation: What It Is and How to Reduce It",
     "category": "Health", "focus_keyword": "chronic inflammation reduction",
     "meta_desc": "Chronic inflammation underlies many modern diseases. Learn what triggers it and which diet, lifestyle, and supplement strategies reduce it effectively."},

    {"title": "The Science of Sleep: How to Get Better Sleep Tonight",
     "category": "Health", "focus_keyword": "how to get better sleep",
     "meta_desc": "Poor sleep affects everything from immunity to mood. Discover the science of sleep cycles and 12 evidence-based tips for deeper, more restorative sleep."},

    {"title": "Back Pain Relief: Causes, Exercises, and Prevention Tips",
     "category": "Health", "focus_keyword": "back pain relief exercises",
     "meta_desc": "Back pain affects 8 in 10 people. Learn the most common causes, effective relief exercises, and prevention strategies to stay pain-free."},

    # ── Health Insurance ─────────────────────────────────────────────────────
    {"title": "How to Choose the Right Health Insurance Plan in 2025",
     "category": "Health Insurance", "focus_keyword": "choose health insurance plan",
     "meta_desc": "Navigating health insurance options is overwhelming. This guide breaks down plan types, key terms, and how to choose the right coverage for your needs."},

    {"title": "HMO vs. PPO vs. EPO: Which Health Insurance Plan is Best?",
     "category": "Health Insurance", "focus_keyword": "HMO vs PPO health insurance",
     "meta_desc": "Confused by HMO, PPO, and EPO plans? We compare costs, flexibility, and coverage so you can make an informed health insurance decision."},

    {"title": "Health Insurance for Self-Employed Workers: A Complete Guide",
     "category": "Health Insurance", "focus_keyword": "health insurance self-employed",
     "meta_desc": "Self-employed? Here's everything you need to know about affordable health insurance options, tax deductions, and how to get covered."},

    {"title": "Understanding Your Deductible, Copay, and Out-of-Pocket Maximum",
     "category": "Health Insurance", "focus_keyword": "health insurance deductible explained",
     "meta_desc": "Confused by insurance jargon? We clearly explain deductibles, copays, coinsurance, and out-of-pocket maximums so you never get surprised by a bill."},

    # ── Smoking ──────────────────────────────────────────────────────────────
    {"title": "How to Quit Smoking: The Most Effective Methods Ranked",
     "category": "Smoking", "focus_keyword": "how to quit smoking",
     "meta_desc": "Ready to quit smoking? We rank the most evidence-based cessation methods—from NRT to varenicline—and share practical tips that actually work."},

    {"title": "What Happens to Your Body When You Quit Smoking (Timeline)",
     "category": "Smoking", "focus_keyword": "quit smoking body changes timeline",
     "meta_desc": "From 20 minutes to 15 years after quitting, here's the remarkable timeline of how your body heals once you stop smoking."},

    {"title": "Vaping vs. Smoking: Which Is Actually Worse for Your Health?",
     "category": "Smoking", "focus_keyword": "vaping vs smoking health risks",
     "meta_desc": "Is vaping a safe alternative to cigarettes? We break down the latest research on relative risks, toxins, and long-term health impacts."},

    {"title": "The Financial Cost of Smoking: How Much Could You Save by Quitting?",
     "category": "Smoking", "focus_keyword": "cost of smoking money",
     "meta_desc": "Beyond health, smoking carries a massive financial burden. Calculate exactly how much you could save by quitting today."},

    # ── AI in Health ─────────────────────────────────────────────────────────
    {"title": "How AI Is Transforming Healthcare: 10 Game-Changing Applications",
     "category": "AI in Health", "focus_keyword": "AI transforming healthcare",
     "meta_desc": "Artificial intelligence is reshaping medicine. Explore 10 ground-breaking AI applications that are improving diagnoses, treatments, and patient outcomes."},

    {"title": "AI-Powered Fitness Apps: Can Technology Replace a Personal Trainer?",
     "category": "AI in Health", "focus_keyword": "AI fitness apps",
     "meta_desc": "Sophisticated AI fitness apps claim to personalise workouts like a human trainer. We assess the benefits, limitations, and best options available."},

    {"title": "The Rise of AI Nutrition Assistants: How They Work and Are They Accurate?",
     "category": "AI in Health", "focus_keyword": "AI nutrition assistant",
     "meta_desc": "AI-powered nutrition apps promise personalised dietary advice. Here's how the technology works and whether it can meaningfully improve your diet."},

    # ── Care ─────────────────────────────────────────────────────────────────
    {"title": "Preventive Healthcare: Why Annual Check-Ups Could Save Your Life",
     "category": "Care", "focus_keyword": "preventive healthcare check-ups",
     "meta_desc": "Preventive care is the most cost-effective way to stay healthy. Learn which screenings, vaccines, and check-ups are recommended at every age."},

    {"title": "How to Care for an Ageing Parent at Home: A Comprehensive Guide",
     "category": "Care", "focus_keyword": "caring for ageing parent at home",
     "meta_desc": "Providing home care for an elderly parent is both rewarding and demanding. This guide covers safety modifications, daily routines, and carer self-care."},

    {"title": "Chronic Disease Management: Building a Routine That Keeps You Well",
     "category": "Care", "focus_keyword": "chronic disease management",
     "meta_desc": "Living with a chronic condition requires structure and strategy. Discover proven daily routines and tools for effective long-term disease management."},
]
