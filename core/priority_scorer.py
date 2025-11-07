"""
Priority Scorer - Calculate complaint priority based on multiple factors
Version: 4.0.0 - Production Ready

New Features:
- ✅ Net voting system (upvotes - downvotes)
- ✅ Image requirement priority boost
- ✅ Time-based escalation (aging complaints)
- ✅ Enhanced scoring transparency
- ✅ Dynamic priority adjustment
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from core.config import Config


class PriorityScorer:
    """
    Calculates complaint priority using multi-factor scoring:
    - Urgency keywords (immediate, critical, etc.)
    - Safety concerns (danger, hazard, etc.)
    - Community impact (net votes: upvotes - downvotes)
    - Sensitive content (disciplinary issues)
    - Image requirement (complaints needing visual evidence)
    - Time factor (aging complaints get priority boost)
    """

    def __init__(self, config: Config):
        self.cfg = config

        # Scoring weights
        self.URGENCY_WEIGHT = 2
        self.SAFETY_WEIGHT = 3
        self.DISCIPLINARY_WEIGHT = 3  # Same as safety
        self.IMAGE_REQUIRED_WEIGHT = 1  # Boost for image-required complaints
        self.MANDATORY_IMAGE_WEIGHT = 2  # Higher boost for mandatory images (fire, broken, etc.)
        
        # Voting system
        self.VOTE_DIVISOR = 10  # 10 net votes = 1 point
        self.MAX_VOTE_POINTS = 3  # Cap at 3 points from votes
        self.MIN_VOTE_POINTS = -2  # Max penalty for negative votes
        
        # Time-based escalation
        self.AGING_THRESHOLD_DAYS = 3  # After 3 days, start aging boost
        self.AGING_WEIGHT = 1  # +1 point for old complaints
        self.CRITICAL_AGING_DAYS = 7  # After 7 days, critical aging

    def calculate_priority(
        self,
        complaint: str,
        upvotes: int = 0,
        downvotes: int = 0,
        category: str = "infrastructure",
        is_confidential: bool = False,
        requires_image: bool = False,
        is_mandatory_image: bool = False,
        created_at: Optional[datetime] = None,
        current_status: str = "raised"
    ) -> Dict[str, Any]:
        """
        Calculate priority level with detailed reasoning.

        Args:
            complaint: Complaint text to analyze
            upvotes: Number of upvotes (for public complaints)
            downvotes: Number of downvotes (for public complaints)
            category: Complaint category (academic/hostel/infrastructure)
            is_confidential: If complaint is confidential/disciplinary
            requires_image: If image is required for this complaint
            is_mandatory_image: If image is mandatory (fire, broken, etc.)
            created_at: When complaint was created (for aging calculation)
            current_status: Current complaint status (raised/opened/reviewed/closed)

        Returns:
            Dict with level, score, reasoning, breakdown, and recommendations
        """
        text = complaint.lower()
        score = 0
        breakdown = []
        recommendations = []

        # Factor 1: Safety concerns (HIGHEST priority)
        if any(k in text for k in self.cfg.safety_keywords):
            safety_points = self.SAFETY_WEIGHT
            score += safety_points
            breakdown.append(f"🚨 Safety concerns detected (+{safety_points})")
            recommendations.append("Immediate action required")

        # Factor 2: Confidential/Disciplinary (HIGH priority)
        if is_confidential or any(k in text for k in self.cfg.privacy_keywords):
            disciplinary_points = self.DISCIPLINARY_WEIGHT
            score += disciplinary_points
            breakdown.append(f"🔒 Sensitive/disciplinary content (+{disciplinary_points})")
            recommendations.append("Confidential handling required")

        # Factor 3: Urgency indicators (MEDIUM priority)
        if any(k in text for k in self.cfg.urgency_keywords):
            urgency_points = self.URGENCY_WEIGHT
            score += urgency_points
            breakdown.append(f"⚡ Urgency keywords detected (+{urgency_points})")

        # Factor 4: Image requirement (adds priority for evidence-based complaints)
        if requires_image:
            if is_mandatory_image:
                image_points = self.MANDATORY_IMAGE_WEIGHT
                breakdown.append(f"📸 Mandatory image required (+{image_points})")
                recommendations.append("Visual evidence mandatory")
            else:
                image_points = self.IMAGE_REQUIRED_WEIGHT
                breakdown.append(f"📷 Image recommended (+{image_points})")
                recommendations.append("Visual evidence recommended")
            score += image_points

        # Factor 5: Community impact via NET votes (VARIABLE)
        net_votes = upvotes - downvotes
        if upvotes > 0 or downvotes > 0:
            # Calculate vote points with min/max bounds
            raw_vote_points = net_votes / self.VOTE_DIVISOR
            vote_points = max(
                self.MIN_VOTE_POINTS,
                min(raw_vote_points, self.MAX_VOTE_POINTS)
            )
            
            if vote_points > 0:
                score += vote_points
                breakdown.append(
                    f"👥 Community support: {upvotes} upvotes, {downvotes} downvotes "
                    f"(net: +{net_votes}) (+{vote_points:.1f})"
                )
            elif vote_points < 0:
                score += vote_points  # This will reduce the score
                breakdown.append(
                    f"👎 Negative community feedback: {upvotes} upvotes, {downvotes} downvotes "
                    f"(net: {net_votes}) ({vote_points:.1f})"
                )
            else:
                breakdown.append(
                    f"➖ Neutral votes: {upvotes} upvotes, {downvotes} downvotes (net: 0)"
                )

        # Factor 6: Time-based escalation (aging complaints)
        if created_at and current_status in ["raised", "opened"]:
            age_days = (datetime.now() - created_at).days
            
            if age_days >= self.CRITICAL_AGING_DAYS:
                aging_points = self.AGING_WEIGHT * 2  # Double boost for critical aging
                score += aging_points
                breakdown.append(
                    f"⏰ Critical aging: {age_days} days old (+{aging_points})"
                )
                recommendations.append(f"URGENT: Complaint pending for {age_days} days")
            elif age_days >= self.AGING_THRESHOLD_DAYS:
                aging_points = self.AGING_WEIGHT
                score += aging_points
                breakdown.append(
                    f"⏱️ Aging complaint: {age_days} days old (+{aging_points})"
                )
                recommendations.append(f"Attention needed: {age_days} days pending")

        # Ensure minimum score of 0
        score = max(0, score)

        # Determine priority level with adjusted thresholds
        if score >= 6:
            level = "Critical"
            priority_emoji = "🔴"
        elif score >= 4:
            level = "High"
            priority_emoji = "🟠"
        elif score >= 2:
            level = "Medium"
            priority_emoji = "🟡"
        else:
            level = "Low"
            priority_emoji = "🟢"

        # Build reasoning
        if not breakdown:
            reasoning = f"Standard {category} complaint with no urgency indicators"
        else:
            reasoning = " | ".join(breakdown)

        # Additional metadata
        result = {
            "level": level,
            "score": round(score, 2),
            "reasoning": reasoning,
            "breakdown": breakdown,
            "category": category,
            "upvotes": upvotes,
            "downvotes": downvotes,
            "net_votes": net_votes if (upvotes > 0 or downvotes > 0) else 0,
            "priority_emoji": priority_emoji,
            "priority_label": f"{priority_emoji} {level} Priority",
            "recommendations": recommendations,
            "requires_image": requires_image,
            "is_mandatory_image": is_mandatory_image
        }

        # Add aging info if applicable
        if created_at:
            age_days = (datetime.now() - created_at).days
            result["age_days"] = age_days
            result["is_aged"] = age_days >= self.AGING_THRESHOLD_DAYS
            result["is_critically_aged"] = age_days >= self.CRITICAL_AGING_DAYS

        return result

    def recalculate_priority_with_votes(
        self,
        existing_priority: Dict[str, Any],
        new_upvotes: int,
        new_downvotes: int
    ) -> Dict[str, Any]:
        """
        Recalculate priority when votes change (for real-time updates).
        
        Args:
            existing_priority: Current priority dict
            new_upvotes: Updated upvote count
            new_downvotes: Updated downvote count
            
        Returns:
            Updated priority dict
        """
        # Extract base score (without vote contribution)
        old_net_votes = existing_priority.get("net_votes", 0)
        old_vote_points = max(
            self.MIN_VOTE_POINTS,
            min(old_net_votes / self.VOTE_DIVISOR, self.MAX_VOTE_POINTS)
        )
        
        base_score = existing_priority["score"] - old_vote_points
        
        # Calculate new vote contribution
        new_net_votes = new_upvotes - new_downvotes
        new_vote_points = max(
            self.MIN_VOTE_POINTS,
            min(new_net_votes / self.VOTE_DIVISOR, self.MAX_VOTE_POINTS)
        )
        
        # Update score
        new_score = base_score + new_vote_points
        new_score = max(0, new_score)
        
        # Determine new level
        if new_score >= 6:
            level = "Critical"
            priority_emoji = "🔴"
        elif new_score >= 4:
            level = "High"
            priority_emoji = "🟠"
        elif new_score >= 2:
            level = "Medium"
            priority_emoji = "🟡"
        else:
            level = "Low"
            priority_emoji = "🟢"
        
        # Update existing priority dict
        existing_priority["score"] = round(new_score, 2)
        existing_priority["level"] = level
        existing_priority["priority_emoji"] = priority_emoji
        existing_priority["priority_label"] = f"{priority_emoji} {level} Priority"
        existing_priority["upvotes"] = new_upvotes
        existing_priority["downvotes"] = new_downvotes
        existing_priority["net_votes"] = new_net_votes
        
        # Update breakdown (replace vote line)
        breakdown = existing_priority["breakdown"]
        breakdown = [b for b in breakdown if not b.startswith("👥") and not b.startswith("👎") and not b.startswith("➖")]
        
        if new_vote_points > 0:
            breakdown.append(
                f"👥 Community support: {new_upvotes} upvotes, {new_downvotes} downvotes "
                f"(net: +{new_net_votes}) (+{new_vote_points:.1f})"
            )
        elif new_vote_points < 0:
            breakdown.append(
                f"👎 Negative community feedback: {new_upvotes} upvotes, {new_downvotes} downvotes "
                f"(net: {new_net_votes}) ({new_vote_points:.1f})"
            )
        else:
            breakdown.append(
                f"➖ Neutral votes: {new_upvotes} upvotes, {new_downvotes} downvotes (net: 0)"
            )
        
        existing_priority["breakdown"] = breakdown
        existing_priority["reasoning"] = " | ".join(breakdown)
        
        return existing_priority

    def get_priority_label(self, level: str) -> str:
        """Get emoji label for priority level"""
        labels = {
            "Critical": "🔴 Critical Priority",
            "High": "🟠 High Priority",
            "Medium": "🟡 Medium Priority",
            "Low": "🟢 Low Priority"
        }
        return labels.get(level, "⚪ Unknown Priority")

    def should_expedite(self, priority_result: Dict[str, Any]) -> bool:
        """Determine if complaint should be expedited (fast-tracked)"""
        return (
            priority_result["score"] >= 6 or 
            priority_result.get("is_critically_aged", False)
        )

    def should_alert_authority(self, priority_result: Dict[str, Any]) -> bool:
        """Determine if authority should receive immediate alert"""
        return (
            priority_result["level"] in ["Critical", "High"] or
            priority_result.get("is_critically_aged", False) or
            any("Safety" in b or "🚨" in b for b in priority_result["breakdown"])
        )

    def get_sla_deadline(
        self, 
        priority_level: str, 
        created_at: datetime
    ) -> datetime:
        """
        Calculate Service Level Agreement (SLA) deadline based on priority.
        
        Args:
            priority_level: Critical/High/Medium/Low
            created_at: When complaint was created
            
        Returns:
            Deadline datetime for resolution
        """
        sla_hours = {
            "Critical": 4,   # 4 hours
            "High": 24,      # 1 day
            "Medium": 72,    # 3 days
            "Low": 168       # 7 days
        }
        
        hours = sla_hours.get(priority_level, 168)
        return created_at + timedelta(hours=hours)

    def is_overdue(
        self, 
        priority_result: Dict[str, Any], 
        created_at: datetime
    ) -> bool:
        """Check if complaint is overdue based on SLA"""
        deadline = self.get_sla_deadline(priority_result["level"], created_at)
        return datetime.now() > deadline
