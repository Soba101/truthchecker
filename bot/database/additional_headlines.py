ADDITIONAL_HEADLINES = [
    {
        "text": "New solar panel technology increases efficiency by 20% using perovskite layers",
        "is_real": True,
        "source": "Scientific American",
        "source_credibility_rating": 8,
        "category": "technology",
        "difficulty": "medium",
        "explanation": "Researchers have been experimenting with perovskite materials to boost photovoltaic efficiency, though commercial adoption is still under development.",
        "detection_tips": [
            "Look for peer-reviewed publications announcing efficiency gains",
            "Check if the breakthrough is described by multiple science outlets",
            "Incremental improvements are common rather than sudden radical jumps"
        ],
        "teaches_concepts": ["technology reporting", "scientific verification", "incremental innovation"],
        "red_flags": [],
        "verification_sources": ["IEEE Spectrum", "Nature Energy", "university press releases"]
    },
    {
        "text": "UN Security Council unanimously approves global ban on autonomous lethal weapons systems",
        "is_real": False,
        "source": "GlobalPoliticsToday.net",
        "source_credibility_rating": 3,
        "category": "politics",
        "difficulty": "hard",
        "explanation": "While there is ongoing debate, the UN has not passed a binding resolution with unanimous support banning autonomous weapons.",
        "detection_tips": [
            "Check official UN press releases",
            "Look for voting records of Security Council resolutions",
            "Verify with reputable international relations outlets"
        ],
        "teaches_concepts": ["international policy", "primary source verification", "misinformation in global affairs"],
        "red_flags": ["unanimous vote claim", "policy extremes", "single-source announcement"],
        "verification_sources": ["UN.org", "BBC", "Reuters"]
    },
    {
        "text": "Breakthrough gene therapy reverses aging in mice, human trials slated next year",
        "is_real": True,
        "source": "Nature Biotechnology",
        "source_credibility_rating": 9,
        "category": "health",
        "difficulty": "medium",
        "explanation": "Gene therapies targeting cellular aging pathways have shown promise in animal studies, but human application remains experimental.",
        "detection_tips": [
            "Check for peer-reviewed animal studies",
            "Human trials require regulatory approval",
            "Radical claims should cite primary research"
        ],
        "teaches_concepts": ["biotech reporting", "animal vs human studies", "regulatory hurdles"],
        "red_flags": [],
        "verification_sources": ["ClinicalTrials.gov", "FDA announcements", "scientific journals"]
    },
    {
        "text": "Major airline announces zero-emission transatlantic flights powered entirely by algae biofuel",
        "is_real": False,
        "source": "EcoFlightsNow.com",
        "source_credibility_rating": 2,
        "category": "environment",
        "difficulty": "hard",
        "explanation": "While biofuels are researched, current technology cannot power long-haul flights solely on algae-based fuel at commercial scale.",
        "detection_tips": [
            "Check for press releases from the airline",
            "Assess feasibility of fuel energy density",
            "Look for coverage by aviation industry outlets"
        ],
        "teaches_concepts": ["feasibility assessment", "greenwashing", "energy density"],
        "red_flags": ["technology leap", "single-source story", "lack of technical detail"],
        "verification_sources": ["IATA", "Aviation Week", "Bloomberg NEF"]
    },
    {
        "text": "Study finds that reading physical books improves sleep quality more than e-readers",
        "is_real": True,
        "source": "Journal of Sleep Research",
        "source_credibility_rating": 7,
        "category": "health",
        "difficulty": "medium",
        "explanation": "Blue light from electronic screens can suppress melatonin production, disturbing sleep; reading paper avoids this effect.",
        "detection_tips": [
            "Look for randomized controlled studies",
            "Check sample size and methodology",
            "Multiple journals should corroborate findings"
        ],
        "teaches_concepts": ["health study interpretation", "blue light effects", "methodology scrutiny"],
        "red_flags": [],
        "verification_sources": ["PubMed", "Harvard Health", "Sleep Foundation"]
    },
    {
        "text": "Global coffee prices plummet 40% after synthetic coffee hits market",
        "is_real": False,
        "source": "MarketBuzzDaily",
        "source_credibility_rating": 4,
        "category": "business",
        "difficulty": "medium",
        "explanation": "While lab-grown coffee startups exist, they have not disrupted global commodity prices at this scale.",
        "detection_tips": [
            "Compare with commodity exchange data",
            "Look for statements from coffee associations",
            "Sudden market shifts require multiple confirmations"
        ],
        "teaches_concepts": ["market data verification", "commodity pricing", "startup impact assessment"],
        "red_flags": ["dramatic percentage change", "single disruptive factor", "lack of exchange data"],
        "verification_sources": ["ICE Futures", "Bloomberg", "Reuters"]
    },
    {
        "text": "Archaeologists uncover lost city beneath Amazon rainforest using LiDAR technology",
        "is_real": True,
        "source": "National Geographic",
        "source_credibility_rating": 9,
        "category": "science",
        "difficulty": "hard",
        "explanation": "Recent LiDAR surveys have revealed complex pre-Columbian settlements hidden by dense rainforest canopy.",
        "detection_tips": [
            "Check for peer-reviewed archaeological reports",
            "Look for satellite or LiDAR imagery",
            "See if multiple academic institutions are involved"
        ],
        "teaches_concepts": ["remote sensing", "archaeological evidence", "multi-disciplinary corroboration"],
        "red_flags": [],
        "verification_sources": ["Science", "PNAS", "university archaeology departments"]
    },
    {
        "text": "Crypto exchange accidentally burns 500 million dollars in user assets during upgrade",
        "is_real": True,
        "source": "CoinDesk",
        "source_credibility_rating": 7,
        "category": "technology",
        "difficulty": "hard",
        "explanation": "Programming errors or smart contract misconfigurations have led to large asset losses in the past within crypto platforms.",
        "detection_tips": [
            "Verify with blockchain transaction records",
            "Check for exchange statements",
            "Look for multiple crypto news outlets covering"
        ],
        "teaches_concepts": ["blockchain transparency", "technology risk", "financial reporting"],
        "red_flags": [],
        "verification_sources": ["Blockchain explorers", "official exchange blog", "major crypto media"]
    },
    {
        "text": "Mars rover detects microbial life signatures in subsurface ice cores",
        "is_real": False,
        "source": "SpaceFrontierNews",
        "source_credibility_rating": 5,
        "category": "science",
        "difficulty": "hard",
        "explanation": "No rover has yet drilled that deep to directly retrieve and analyze subsurface ice for life; confirmations would require extensive peer review.",
        "detection_tips": [
            "Check NASA press conferences",
            "Search for peer-reviewed publications",
            "Extraordinary claims need extraordinary evidence"
        ],
        "teaches_concepts": ["space exploration", "extraordinary claims", "scientific validation"],
        "red_flags": ["life on Mars claim", "single outlet scoop", "no peer review"],
        "verification_sources": ["NASA", "ESA", "Nature Astronomy"]
    },
    {
        "text": "New cybersecurity law allows governments to install surveillance software on all personal devices",
        "is_real": False,
        "source": "TechPrivacyWatch",
        "source_credibility_rating": 3,
        "category": "politics",
        "difficulty": "hard",
        "explanation": "No major democracy has passed blanket legislation permitting universal device surveillance without due process; such a law would face intense scrutiny.",
        "detection_tips": [
            "Check official government gazettes or legal texts",
            "Look for reactions from civil liberties groups",
            "Verify with major news outlets"
        ],
        "teaches_concepts": ["legislative verification", "digital rights", "policy analysis"],
        "red_flags": ["broad authority claim", "lack of official citation", "human rights concerns"],
        "verification_sources": ["official government websites", "EFF", "BBC"]
    },
    {
        "text": "Ocean currents show unprecedented slowdown threatening global climate patterns, scientists warn",
        "is_real": True,
        "source": "Nature Climate Change",
        "source_credibility_rating": 9,
        "category": "environment",
        "difficulty": "hard",
        "explanation": "Recent studies point to a potential weakening of the Atlantic Meridional Overturning Circulation with significant climate impacts.",
        "detection_tips": [
            "Look for publication in high-impact journals",
            "Compare data with historical records",
            "Seek consensus among climatologists"
        ],
        "teaches_concepts": ["climate data analysis", "peer review", "long-term trends"],
        "red_flags": [],
        "verification_sources": ["IPCC", "NOAA", "academic journals"]
    },
    {
        "text": "Breakthrough battery charges electric cars fully in 5 minutes, commercial release this year",
        "is_real": False,
        "source": "FastTechNews",
        "source_credibility_rating": 4,
        "category": "technology",
        "difficulty": "medium",
        "explanation": "While fast-charging research exists, achieving full EV charge in 5 minutes with current infrastructure is unrealistic for near-term commercial rollout.",
        "detection_tips": [
            "Look for statements from major automakers",
            "Assess compatibility with existing chargers",
            "Check for independent testing results"
        ],
        "teaches_concepts": ["technology feasibility", "infrastructure limitations", "industry vetting"],
        "red_flags": ["too good to be true", "lack of prototype details", "no third-party validation"],
        "verification_sources": ["SAE International", "IEEE", "automotive press"]
    },
    {
        "text": "World chess champion defeated by quantum computer running advanced AI algo",
        "is_real": False,
        "source": "QuantumEdgeTimes",
        "source_credibility_rating": 5,
        "category": "technology",
        "difficulty": "hard",
        "explanation": "Quantum computers are not yet advanced enough with error correction to play complex games like chess at champion level.",
        "detection_tips": [
            "Check announcements from quantum labs",
            "Review match footage or official tournament records",
            "Verify with recognized chess organizations"
        ],
        "teaches_concepts": ["technology maturity", "verification with governing bodies", "AI hype skepticism"],
        "red_flags": ["quantum supremacy claim", "no technical details", "lack of FIDE confirmation"],
        "verification_sources": ["FIDE", "Nature", "IBM Research"]
    },
    {
        "text": "Researchers develop plant that glows brightly enough to replace indoor lighting",
        "is_real": True,
        "source": "Science Advances",
        "source_credibility_rating": 8,
        "category": "science",
        "difficulty": "medium",
        "explanation": "Synthetic biology experiments have produced bioluminescent plants, though brightness remains a challenge for practical lighting.",
        "detection_tips": [
            "Read the experimental brightness measurements",
            "Cross-check with energy efficiency standards",
            "Look for commercialization timelines"
        ],
        "teaches_concepts": ["synthetic biology", "scalability", "experimental limitations"],
        "red_flags": [],
        "verification_sources": ["MIT News", "Nature Plants", "peer-reviewed articles"]
    },
    {
        "text": "Global literacy rate surpasses 95% according to latest UN report",
        "is_real": False,
        "source": "WorldEducationDaily",
        "source_credibility_rating": 4,
        "category": "news",
        "difficulty": "hard",
        "explanation": "UNESCO statistics show global adult literacy hovering around 86%; a sudden jump to 95% is unsubstantiated.",
        "detection_tips": [
            "Check UNESCO Institute for Statistics",
            "Compare with previous year's data",
            "Large global changes happen gradually"
        ],
        "teaches_concepts": ["data verification", "statistical trends", "global reporting"],
        "red_flags": ["too large change", "lack of regional breakdown", "single source"],
        "verification_sources": ["UNESCO", "World Bank", "OECD"]
    },
    {
        "text": "Fusion reactor maintains net energy gain for 8 hours in historic experiment",
        "is_real": True,
        "source": "IEEE Spectrum",
        "source_credibility_rating": 8,
        "category": "science",
        "difficulty": "hard",
        "explanation": "Long-pulse fusion experiments aim to demonstrate sustained net energy, but such breakthroughs are rare and under intense review.",
        "detection_tips": [
            "Verify with laboratory press releases",
            "Check for independent replication",
            "Look for peer-reviewed data release"
        ],
        "teaches_concepts": ["energy research", "experimental replication", "scientific scrutiny"],
        "red_flags": [],
        "verification_sources": ["ITER", "Nature Physics", "DOE"]
    },
    {
        "text": "Facebook to introduce subscription fee for all users starting next month",
        "is_real": False,
        "source": "SocialMediaWatch",
        "source_credibility_rating": 3,
        "category": "business",
        "difficulty": "medium",
        "explanation": "Rumors about blanket subscription fees circulate periodically; Meta's revenue model relies heavily on advertising.",
        "detection_tips": [
            "Check official Meta newsroom",
            "Look for SEC filings mentioning new revenue streams",
            "Consider business model incentives"
        ],
        "teaches_concepts": ["corporate communications", "business model analysis", "rumor debunking"],
        "red_flags": ["no official announcement", "overnight change", "viral social media posts"],
        "verification_sources": ["Meta", "SEC", "WSJ"]
    },
    {
        "text": "Rare earth asteroid estimated at 10 trillion dollars to be captured and mined by private company",
        "is_real": False,
        "source": "SpaceMiningDaily",
        "source_credibility_rating": 4,
        "category": "business",
        "difficulty": "hard",
        "explanation": "Asteroid mining remains theoretical with significant technical barriers; no private firm has capability to capture an asteroid today.",
        "detection_tips": [
            "Check company technology readiness",
            "Look for mission timetable",
            "Assess coverage by reputable space agencies"
        ],
        "teaches_concepts": ["feasibility analysis", "space technology", "investment skepticism"],
        "red_flags": ["huge monetary figure", "no prototype", "speculative timeline"],
        "verification_sources": ["NASA", "ESA", "SpaceNews"]
    },
    {
        "text": "WHO confirms new airborne virus with 70% mortality spreading globally",
        "is_real": False,
        "source": "HealthAlert24",
        "source_credibility_rating": 2,
        "category": "health",
        "difficulty": "hard",
        "explanation": "WHO emergency declarations are formal processes; such a lethal virus would dominate global news.",
        "detection_tips": [
            "Check WHO Situation Reports",
            "Look for coordinated government responses",
            "Verify travel advisories and scientific briefings"
        ],
        "teaches_concepts": ["official health communication", "pandemic protocols", "source credibility"],
        "red_flags": ["panic tone", "extreme mortality", "lack of mainstream coverage"],
        "verification_sources": ["WHO", "CDC", "Reuters"]
    },
    {
        "text": "Researchers create plastic-eating enzyme that degrades bottles in 24 hours",
        "is_real": True,
        "source": "Guardian",
        "source_credibility_rating": 8,
        "category": "science",
        "difficulty": "medium",
        "explanation": "Enzymatic recycling advances have produced variants capable of rapid PET breakdown under controlled conditions.",
        "detection_tips": [
            "Look at laboratory conditions vs real-world scale",
            "Check for commercial partners",
            "Read peer-reviewed enzyme studies"
        ],
        "teaches_concepts": ["biotechnology", "scaling technology", "environmental solutions"],
        "red_flags": [],
        "verification_sources": ["Science", "Nature", "company press releases"]
    },
    {
        "text": "Global oil demand falls to 1990 levels due to rapid renewable adoption, IEA reports",
        "is_real": False,
        "source": "GreenEnergyHub",
        "source_credibility_rating": 4,
        "category": "environment",
        "difficulty": "medium",
        "explanation": "While renewable energy is growing, oil demand remains high; a drop to 1990 levels would require extraordinary economic shifts.",
        "detection_tips": [
            "Check IEA official statistics",
            "Compare year-on-year demand charts",
            "Look for corroborating economic indicators"
        ],
        "teaches_concepts": ["data literacy", "energy economics", "trend verification"],
        "red_flags": ["extreme change", "single-source claim", "lack of economic context"],
        "verification_sources": ["IEA", "OPEC", "Bloomberg"]
    },
    {
        "text": "Artificial island city built in Pacific to house climate refugees opens to first residents",
        "is_real": True,
        "source": "BBC",
        "source_credibility_rating": 8,
        "category": "news",
        "difficulty": "hard",
        "explanation": "Several nations are investing in floating architecture for rising sea levels; pilot projects have begun accepting limited populations.",
        "detection_tips": [
            "Look for government partnerships",
            "Check satellite imagery",
            "Seek NGO reports on climate adaptation"
        ],
        "teaches_concepts": ["climate adaptation", "infrastructure scale", "project verification"],
        "red_flags": [],
        "verification_sources": ["UN Habitat", "architectural journals", "major news outlets"]
    },
    {
        "text": "FDA approves lab-grown chicken for nationwide sale in supermarkets",
        "is_real": True,
        "source": "Washington Post",
        "source_credibility_rating": 8,
        "category": "business",
        "difficulty": "medium",
        "explanation": "Regulators have begun approving cultivated meat, though distribution scale remains limited initially.",
        "detection_tips": [
            "Check official FDA announcements",
            "Look for company names and pilot production capacity",
            "Assess distribution timelines"
        ],
        "teaches_concepts": ["regulatory process", "food tech", "commercial rollout"],
        "red_flags": [],
        "verification_sources": ["FDA.gov", "USDA", "industry publications"]
    },
    {
        "text": "Ancient scroll burned in Vesuvius eruption read for first time using particle accelerator",
        "is_real": True,
        "source": "Nature Communications",
        "source_credibility_rating": 9,
        "category": "science",
        "difficulty": "hard",
        "explanation": "Advanced imaging and machine learning have enabled non-destructive reading of carbonized scrolls from Herculaneum.",
        "detection_tips": [
            "Look for interdisciplinary research teams",
            "Check for open data releases",
            "Read methods using X-ray phase-contrast tomography"
        ],
        "teaches_concepts": ["cultural heritage tech", "imaging techniques", "interdisciplinary science"],
        "red_flags": [],
        "verification_sources": ["universities", "synchrotron facility press", "peer-reviewed journals"]
    },
    {
        "text": "All EU countries agree to abolish paper currency by 2026, switch to digital euro only",
        "is_real": False,
        "source": "FinanceFutureDaily",
        "source_credibility_rating": 3,
        "category": "politics",
        "difficulty": "hard",
        "explanation": "Digital euro proposals exist, but unanimous agreement to eliminate cash on such a short timeline is unrealistic.",
        "detection_tips": [
            "Check European Central Bank statements",
            "Look for individual member state legislation",
            "Assess economic analysis from credible think tanks"
        ],
        "teaches_concepts": ["policy feasibility", "monetary systems", "EU governance"],
        "red_flags": ["unanimous claim", "tight timeline", "lack of official sources"],
        "verification_sources": ["ECB", "EU Parliament", "Financial Times"]
    },
    {
        "text": "Scientists teleport quantum information between satellites in orbit, setting new record",
        "is_real": True,
        "source": "Phys.org",
        "source_credibility_rating": 7,
        "category": "science",
        "difficulty": "medium",
        "explanation": "Quantum entanglement experiments have achieved space-based teleportation increasing distances for secure communication research.",
        "detection_tips": [
            "Review published experiment parameters",
            "Look for collaboration among space agencies",
            "Check for peer-reviewed results"
        ],
        "teaches_concepts": ["quantum communication", "experimental validation", "technology milestones"],
        "red_flags": [],
        "verification_sources": ["Nature Photonics", "Chinese Academy of Sciences", "ESA"]
    },
    {
        "text": "Major city bans private car ownership, shifts entirely to public transport and bikes",
        "is_real": False,
        "source": "UrbanTrendMag",
        "source_credibility_rating": 4,
        "category": "environment",
        "difficulty": "hard",
        "explanation": "Cities introduce low-emission zones, but a full ban on private ownership is unprecedented and legally challenging.",
        "detection_tips": [
            "Check municipal legislation",
            "Look for phased timelines and exemptions",
            "Verify with local news and residents"
        ],
        "teaches_concepts": ["policy analysis", "urban planning", "stakeholder impact"],
        "red_flags": ["absolute language", "lack of legal framework", "no stakeholder pushback"],
        "verification_sources": ["city council records", "transport journals", "BBC"]
    },
    {
        "text": "New meta-analysis shows daily meditation rewires brain in 8 weeks, improving focus by 30%",
        "is_real": True,
        "source": "Psychological Science",
        "source_credibility_rating": 7,
        "category": "health",
        "difficulty": "medium",
        "explanation": "Multiple MRI studies have observed structural brain changes associated with mindfulness practices over two months.",
        "detection_tips": [
            "Check meta-analysis methodology",
            "Look at effect size across studies",
            "Consider variability in practice adherence"
        ],
        "teaches_concepts": ["meta-analysis understanding", "effect size", "neuroplasticity"],
        "red_flags": [],
        "verification_sources": ["PubMed", "NIH", "journals"]
    },
    {
        "text": "Firefighters use autonomous drone swarm to contain record-breaking wildfire in 24 hours",
        "is_real": False,
        "source": "TechRescueNews",
        "source_credibility_rating": 4,
        "category": "technology",
        "difficulty": "hard",
        "explanation": "Drone swarms assist firefighting, but fully autonomous containment at this scale is beyond current capabilities.",
        "detection_tips": [
            "Check incident reports from fire authorities",
            "Look for manufacturer technology demonstrations",
            "Assess logistical feasibility"
        ],
        "teaches_concepts": ["technology readiness levels", "emergency response", "feasibility checks"],
        "red_flags": ["record-breaking claim", "complete automation", "lack of official confirmation"],
        "verification_sources": ["US Forest Service", "Fire Technology Journal", "Reuters"]
    },
    {
        "text": "Largest genetic study links gut microbiome diversity to mental health outcomes",
        "is_real": True,
        "source": "Cell",
        "source_credibility_rating": 9,
        "category": "health",
        "difficulty": "hard",
        "explanation": "Emerging research explores the gut-brain axis, with large cohort studies examining microbiome correlations with anxiety and depression.",
        "detection_tips": [
            "Check sample size and statistical significance",
            "Look for replication in other populations",
            "Review confounding factors"
        ],
        "teaches_concepts": ["statistical analysis", "correlation vs causation", "multidisciplinary research"],
        "red_flags": [],
        "verification_sources": ["Nature", "NIH", "WHO"]
    },
    {
        "text": "Apple announces brain-computer interface iPhone controlled by thoughts",
        "is_real": False,
        "source": "TechRumorBlog",
        "source_credibility_rating": 2,
        "category": "technology",
        "difficulty": "medium",
        "explanation": "While Apple researches accessibility tech, direct thought control requires invasive or specialized sensors, not consumer-ready.",
        "detection_tips": [
            "Check official Apple keynote transcripts",
            "Look for patent filings",
            "Consider practical manufacturing challenges"
        ],
        "teaches_concepts": ["corporate source checking", "technology hype", "patent vs product"],
        "red_flags": ["no demonstration", "too futuristic", "rumor source"],
        "verification_sources": ["Apple.com", "WSJ", "Bloomberg"]
    },
    {
        "text": "Global bee population increases 15% after widespread wildflower initiatives, UN data shows",
        "is_real": True,
        "source": "UN Environment Programme",
        "source_credibility_rating": 8,
        "category": "environment",
        "difficulty": "medium",
        "explanation": "Conservation programs can yield regional bee recovery; global statistics may show modest gains due to coordinated efforts.",
        "detection_tips": [
            "Review methodology of population estimates",
            "Check regional variance",
            "Look for independent ecological assessments"
        ],
        "teaches_concepts": ["environmental statistics", "biodiversity", "conservation metrics"],
        "red_flags": [],
        "verification_sources": ["FAO", "scientific journals", "conservation NGOs"]
    },
    {
        "text": "Internet to switch from IPv6 to IPv7 standard next year, impacting all devices",
        "is_real": False,
        "source": "NetTechWorld",
        "source_credibility_rating": 4,
        "category": "technology",
        "difficulty": "hard",
        "explanation": "IPv6 adoption is still ongoing; no official standard named IPv7 has been ratified by IETF.",
        "detection_tips": [
            "Check IETF RFC publications",
            "Look for statements from major ISPs",
            "Assess adoption readiness"
        ],
        "teaches_concepts": ["standards bodies", "technology adoption", "version naming"],
        "red_flags": ["sudden mandatory switch", "non-existent standard", "lack of vendor preparation"],
        "verification_sources": ["IETF", "ICANN", "network engineering journals"]
    },
    {
        "text": "Cancer vaccine shows 100% success rate in early human trials",
        "is_real": False,
        "source": "HealthBreakthroughsNow",
        "source_credibility_rating": 3,
        "category": "health",
        "difficulty": "hard",
        "explanation": "Medical trials rarely report 100% efficacy; early phase studies focus on safety and small cohorts.",
        "detection_tips": [
            "Check clinical trial registries",
            "Look for peer-reviewed results",
            "Evaluate sample size"
        ],
        "teaches_concepts": ["clinical trial phases", "statistical significance", "critical health literacy"],
        "red_flags": ["perfect success", "small study", "lack of peer review"],
        "verification_sources": ["ClinicalTrials.gov", "Lancet", "FDA"]
    },
    {
        "text": "World's first 3D-printed steel bridge opens to traffic in Amsterdam",
        "is_real": True,
        "source": "CNN",
        "source_credibility_rating": 7,
        "category": "technology",
        "difficulty": "medium",
        "explanation": "Engineers have deployed 3D-printed metal pedestrian bridges using robotic welding technology.",
        "detection_tips": [
            "Look for municipal inauguration events",
            "Check engineering firm publications",
            "Verify load testing certifications"
        ],
        "teaches_concepts": ["additive manufacturing", "infrastructure", "engineering innovation"],
        "red_flags": [],
        "verification_sources": ["engineering journals", "city press releases", "BBC"]
    },
    {
        "text": "Study shows people can learn language during REM sleep using ultrasonic stimulation",
        "is_real": False,
        "source": "DreamScientistBlog",
        "source_credibility_rating": 2,
        "category": "science",
        "difficulty": "medium",
        "explanation": "While some memory consolidation occurs during sleep, complex language acquisition requires conscious practice.",
        "detection_tips": [
            "Check existence of peer-reviewed study",
            "Evaluate experimental controls",
            "Look for review articles"
        ],
        "teaches_concepts": ["learning science", "research replication", "critical evaluation"],
        "red_flags": ["extraordinary learning claim", "no replication", "popular media exaggeration"],
        "verification_sources": ["Psychology journals", "academic conferences", "Nature Neuroscience"]
    },
    {
        "text": "Electric air taxi completes first commercial passenger flight across New York City",
        "is_real": True,
        "source": "Bloomberg",
        "source_credibility_rating": 8,
        "category": "business",
        "difficulty": "hard",
        "explanation": "Urban air mobility trials are underway; limited commercial demonstrations have occurred under special flight approvals.",
        "detection_tips": [
            "Check FAA special certificates",
            "Look for passenger testimonials",
            "Verify with aviation regulators"
        ],
        "teaches_concepts": ["emerging tech regulation", "pilot projects", "transport innovation"],
        "red_flags": [],
        "verification_sources": ["FAA", "EASA", "Aviation Week"]
    },
    {
        "text": "Largest coral reef restoration effort sees 85% survival after 2 years, scientists report",
        "is_real": True,
        "source": "Science",
        "source_credibility_rating": 9,
        "category": "environment",
        "difficulty": "medium",
        "explanation": "Restoration projects using coral nurseries have reported high survival rates with new methodologies.",
        "detection_tips": [
            "Review longitudinal data",
            "Check for ecological peer review",
            "Look for corroborating environmental NGOs"
        ],
        "teaches_concepts": ["environmental restoration", "long-term monitoring", "ecosystem resilience"],
        "red_flags": [],
        "verification_sources": ["NOAA", "peer-reviewed journals", "conservation reports"]
    },
    {
        "text": "New legislation mandates four-day workweek countrywide without salary reduction",
        "is_real": False,
        "source": "WorkLifeNews",
        "source_credibility_rating": 3,
        "category": "politics",
        "difficulty": "hard",
        "explanation": "Some nations pilot shorter workweeks, but nationwide mandatory adoption is still experimental and debated.",
        "detection_tips": [
            "Check parliamentary records",
            "Look for phased implementation plans",
            "Assess coverage by business chambers"
        ],
        "teaches_concepts": ["policy trial vs law", "economic impact", "legislative process"],
        "red_flags": ["immediate enforcement", "lack of stakeholder consultation", "no official bill text"],
        "verification_sources": ["government websites", "ILO", "Reuters"]
    },
    {
        "text": "AI writes and directs feature film that wins Cannes Palme d'Or",
        "is_real": False,
        "source": "FilmTechTrends",
        "source_credibility_rating": 4,
        "category": "entertainment",
        "difficulty": "hard",
        "explanation": "AI assists in film production, but full creative control and major festival victory remains speculative.",
        "detection_tips": [
            "Check Cannes official winners list",
            "Look for director credits",
            "Verify with industry trades"
        ],
        "teaches_concepts": ["creative AI limits", "award verification", "industry fact-checking"],
        "red_flags": ["sensational AI claim", "lack of human attribution", "no festival coverage"],
        "verification_sources": ["Cannes", "Variety", "Hollywood Reporter"]
    },
    {
        "text": "Breakthrough transparent solar windows generate power while letting in light",
        "is_real": True,
        "source": "Popular Science",
        "source_credibility_rating": 7,
        "category": "technology",
        "difficulty": "medium",
        "explanation": "Researchers develop photovoltaic coatings that absorb ultraviolet and infrared, keeping visible light transmission high.",
        "detection_tips": [
            "Look for efficiency metrics",
            "Check for commercialization partners",
            "Review durability testing data"
        ],
        "teaches_concepts": ["material science", "commercial scalability", "tech innovation"],
        "red_flags": [],
        "verification_sources": ["Nature Energy", "IEEE", "company press releases"]
    },
    {
        "text": "Genetically modified mosquitoes eradicate malaria in entire region within 3 years",
        "is_real": False,
        "source": "GlobalHealthFuture",
        "source_credibility_rating": 4,
        "category": "health",
        "difficulty": "hard",
        "explanation": "Field trials of gene-drive mosquitoes are ongoing; complete regional eradication has not yet been achieved or documented.",
        "detection_tips": [
            "Check WHO malaria reports",
            "Review gene-drive trial results",
            "Look for ecological impact studies"
        ],
        "teaches_concepts": ["gene-drive technology", "public health data", "intervention outcomes"],
        "red_flags": ["absolute eradication", "short timeframe", "lack of independent verification"],
        "verification_sources": ["WHO", "Lancet", "nature journals"]
    },
    {
        "text": "First quantum internet backbone goes live connecting three continents",
        "is_real": False,
        "source": "QuantumNetNews",
        "source_credibility_rating": 5,
        "category": "technology",
        "difficulty": "hard",
        "explanation": "Quantum key distribution links exist regionally; a global backbone spanning continents is not yet operational.",
        "detection_tips": [
            "Check telecom infrastructure announcements",
            "Look for details on repeater technology",
            "Verify with national labs involved in quantum networks"
        ],
        "teaches_concepts": ["technology maturity", "infrastructure scale", "scientific collaboration"],
        "red_flags": ["continent-wide claim", "lack of technical specifications", "no governmental partnerships"],
        "verification_sources": ["Nature", "IEEE", "government research labs"]
    },
    {
        "text": "Researchers teach AI to decode thoughts into text with 95% accuracy",
        "is_real": True,
        "source": "Nature Neuroscience",
        "source_credibility_rating": 9,
        "category": "scientific",
        "difficulty": "medium",
        "explanation": "Brain-computer interfacing has reached high accuracy in controlled experiments translating neural signals to text for paralyzed patients.",
        "detection_tips": [
            "Assess participant count",
            "Look for invasive vs non-invasive methods",
            "Check ethical approval documentation"
        ],
        "teaches_concepts": ["BCI", "accuracy factors", "clinical translation"],
        "red_flags": [],
        "verification_sources": ["Nature Neuroscience", "NIH", "peer-reviewed papers"]
    },
    {
        "text": "Entire internet records stored on DNA strands fitting in a shoebox",
        "is_real": False,
        "source": "BioTechHype",
        "source_credibility_rating": 3,
        "category": "science",
        "difficulty": "hard",
        "explanation": "DNA storage density is high, but cost and sequencing requirements make archiving at internet scale impractical currently.",
        "detection_tips": [
            "Check data density calculations",
            "Assess cost analysis",
            "Look at write/read speeds"
        ],
        "teaches_concepts": ["data storage tech", "scalability", "cost evaluation"],
        "red_flags": ["hyperbolic capacity claim", "ignores economics", "lack of prototype"],
        "verification_sources": ["Microsoft Research", "Science", "Nature Biotechnology"]
    },
    {
        "text": "World's first carbon-negative cement plant begins full-scale operations",
        "is_real": True,
        "source": "Financial Times",
        "source_credibility_rating": 8,
        "category": "business",
        "difficulty": "medium",
        "explanation": "Innovative processes using industrial capture mineralize CO2 during curing resulting in net-negative emissions cement.",
        "detection_tips": [
            "Check life-cycle assessment reports",
            "Look for third-party verification",
            "Assess production capacity"
        ],
        "teaches_concepts": ["industrial decarbonization", "LCAs", "sustainability verification"],
        "red_flags": [],
        "verification_sources": ["IEA", "industry analysts", "scientific journals"]
    },
    {
        "text": "Massive solar flare permanently knocks out half of Earth's satellites",
        "is_real": False,
        "source": "SpaceStormAlert",
        "source_credibility_rating": 4,
        "category": "science",
        "difficulty": "hard",
        "explanation": "Geomagnetic storms can damage satellites, but redundancy and protective measures make loss of half the fleet improbable.",
        "detection_tips": [
            "Check NOAA space weather alerts",
            "Look for satellite operator statements",
            "Verify with multiple space agencies"
        ],
        "teaches_concepts": ["space weather", "risk assessment", "technical resilience"],
        "red_flags": ["extreme impact", "single incident claim", "lack of official confirmation"],
        "verification_sources": ["NOAA", "NASA", "ESA"]
    },
    {
        "text": "Universal flu vaccine approved after decade-long trials",
        "is_real": True,
        "source": "New England Journal of Medicine",
        "source_credibility_rating": 9,
        "category": "health",
        "difficulty": "hard",
        "explanation": "Researchers aim to create vaccines targeting conserved influenza regions; late-stage trials show promise.",
        "detection_tips": [
            "Check phase 3 trial results",
            "Verify regulatory approvals",
            "Assess production ramp-up timelines"
        ],
        "teaches_concepts": ["vaccine development", "clinical evidence", "public health"],
        "red_flags": [],
        "verification_sources": ["FDA", "WHO", "peer-reviewed journals"]
    },
    {
        "text": "Himalayan glacier melts reveal ancient virus reanimating in laboratory tests",
        "is_real": False,
        "source": "ClimateMysteryNews",
        "source_credibility_rating": 3,
        "category": "science",
        "difficulty": "hard",
        "explanation": "While ancient pathogens can be preserved in ice, deliberate reanimation poses extreme biosafety hurdles and would face strict controls.",
        "detection_tips": [
            "Check biosafety level designations",
            "Look for statements from research ethics boards",
            "Verify publication in peer-reviewed virology journals"
        ],
        "teaches_concepts": ["biosecurity", "risk communication", "scientific ethics"],
        "red_flags": ["sensational fear", "lack of lab details", "no authority oversight"],
        "verification_sources": ["CDC", "Nature", "WHO"]
    },
    {
        "text": "International consortium launches project to block sunlight with space mirrors to combat warming",
        "is_real": False,
        "source": "GeoEngineeringToday",
        "source_credibility_rating": 4,
        "category": "environment",
        "difficulty": "hard",
        "explanation": "Solar geoengineering remains in proposal stage; deploying giant mirrors requires exorbitant costs and political consensus not yet achieved.",
        "detection_tips": [
            "Check funding allocations",
            "Look for government partnerships",
            "Assess technical feasibility reports"
        ],
        "teaches_concepts": ["geoengineering", "cost-benefit analysis", "international governance"],
        "red_flags": ["massive scale", "no regulatory framework", "single organization claim"],
        "verification_sources": ["IPCC", "scientific journals", "policy institutes"]
    },
    {
        "text": "Scientists discover room-temperature superconductor working at ambient pressure",
        "is_real": False,
        "source": "PhysicsFrontier",
        "source_credibility_rating": 5,
        "category": "science",
        "difficulty": "hard",
        "explanation": "Room-temperature superconductivity claims undergo rigorous scrutiny; ambient pressure demonstration remains unconfirmed.",
        "detection_tips": [
            "Check replication attempts",
            "Review material synthesis details",
            "Look for publication in high-impact journals"
        ],
        "teaches_concepts": ["scientific replication", "materials science", "critical review"],
        "red_flags": ["extraordinary claim", "limited data", "no independent confirmation"],
        "verification_sources": ["Nature", "Science", "APS meetings"]
    },
    {
        "text": "Global cyberattack shuts down 70% of power grids simultaneously",
        "is_real": False,
        "source": "CyberAlertNews",
        "source_credibility_rating": 3,
        "category": "technology",
        "difficulty": "hard",
        "explanation": "Power grids are regionally segmented; a single attack causing simultaneous global failure is highly improbable.",
        "detection_tips": [
            "Check regional grid operators",
            "Look for government emergency responses",
            "Verify with cybersecurity agencies"
        ],
        "teaches_concepts": ["critical infrastructure", "attack surface", "resilience engineering"],
        "red_flags": ["global scale", "single event", "lack of authoritative confirmation"],
        "verification_sources": ["CISA", "ENISA", "Reuters"]
    },
    {
        "text": "Microbiologists revive 50-million-year-old spores that digest plastic",
        "is_real": True,
        "source": "Science Daily",
        "source_credibility_rating": 7,
        "category": "science",
        "difficulty": "medium",
        "explanation": "Extremophiles can survive in dormant states; novel enzymes may degrade plastic under lab conditions.",
        "detection_tips": [
            "Examine contamination controls",
            "Check enzymatic degradation rate",
            "Look for follow-up studies"
        ],
        "teaches_concepts": ["extremophile biology", "plastic degradation", "lab protocol"],
        "red_flags": [],
        "verification_sources": ["peer-reviewed journals", "university press releases", "Nature Microbiology"]
    },
    {
        "text": "New open-source algorithm compresses data by 99% without loss, revolutionizing storage",
        "is_real": False,
        "source": "TechAlgoForum",
        "source_credibility_rating": 2,
        "category": "technology",
        "difficulty": "medium",
        "explanation": "Lossless compression ratios above certain entropy limits are impossible for arbitrary data sets; claims violate information theory.",
        "detection_tips": [
            "Check algorithm benchmarks",
            "Look for peer review",
            "Assess performance on diverse datasets"
        ],
        "teaches_concepts": ["information theory", "compression limits", "scientific skepticism"],
        "red_flags": ["too good to be true", "no source code", "no independent testing"],
        "verification_sources": ["ACM Digital Library", "IEEE", "specialist blogs"]
    },
    {
        "text": "Scientists map entire human brain connectome at synapse resolution",
        "is_real": True,
        "source": "Nature",
        "source_credibility_rating": 9,
        "category": "science",
        "difficulty": "hard",
        "explanation": "Efforts like the Human Connectome Project produce high-resolution neural maps; full synapse-level mapping is a massive computational challenge but early drafts emerge.",
        "detection_tips": [
            "Check dataset size and accessibility",
            "Look for imaging techniques employed",
            "Assess computing resources described"
        ],
        "teaches_concepts": ["neuroinformatics", "big data", "research scale"],
        "red_flags": [],
        "verification_sources": ["NIH", "Nature", "Science"]
    },
    {
        "text": "Largest online encyclopedia to be curated entirely by AI editors by 2025",
        "is_real": False,
        "source": "AIKnowledgeHub",
        "source_credibility_rating": 3,
        "category": "technology",
        "difficulty": "medium",
        "explanation": "AI assists human editors but full replacement raises bias and accuracy concerns; no such plan is announced by Wikimedia.",
        "detection_tips": [
            "Check Wikimedia Foundation statements",
            "Look for community approval processes",
            "Assess feasibility of automated fact-checking"
        ],
        "teaches_concepts": ["AI limitations", "community governance", "knowledge reliability"],
        "red_flags": ["full automation", "short timeline", "lack of stakeholder input"],
        "verification_sources": ["Wikimedia", "reliable tech media", "academic studies"]
    }
]