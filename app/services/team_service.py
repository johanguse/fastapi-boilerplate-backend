from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.invitation import Invitation
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.team import TeamCreate, TeamInvite
from app.services import activity_log_service
from app.utils.email import send_invitation_email


def create_team(db: Session, team: TeamCreate, current_user: User):
    db_team = Team(name=team.name)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)

    # Add the creator as an admin of the team
    db_team_member = TeamMember(
        team_id=db_team.id, user_id=current_user.id, role='admin'
    )
    db.add(db_team_member)
    db.commit()

    return db_team


def get_team(db: Session, team_id: int):
    return db.query(Team).filter(Team.id == team_id).first()


def is_team_admin(db: Session, team: Team, user: User):
    team_member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team.id,
            TeamMember.user_id == user.id,
            TeamMember.role == 'admin',
        )
        .first()
    )
    return team_member is not None


def is_team_member(db: Session, team: Team, user: User):
    team_member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team.id, TeamMember.user_id == user.id)
        .first()
    )
    return team_member is not None


def invite_team_member(
    db: Session, team: Team, invite: TeamInvite, inviter: User, ip_address: str
):
    # Check if the user is already a member of the team
    existing_member = (
        db.query(TeamMember)
        .join(User)
        .filter(TeamMember.team_id == team.id, User.email == invite.email)
        .first()
    )
    if existing_member:
        raise ValueError('User is already a member of this team')

    # Check if there's an existing invitation
    existing_invitation = (
        db.query(Invitation)
        .filter(
            Invitation.team_id == team.id, Invitation.email == invite.email
        )
        .first()
    )
    if existing_invitation:
        raise ValueError('An invitation has already been sent to this email')

    # Create the invitation
    invitation = Invitation(
        team_id=team.id,
        email=invite.email,
        role=invite.role,
        invited_by_id=inviter.id,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    # Send invitation email
    send_invitation_email(
        invite.email, inviter.email, team.name, settings.FRONTEND_URL
    )

    # Log the activity
    activity_log_service.log_activity(
        db,
        None,  # No project_id for team invitations
        inviter,
        f'Invited {invite.email} to team {team.name} with role {invite.role}',
        ip_address,
    )

    return invitation


def get_team_members(db: Session, team: Team):
    return db.query(TeamMember).filter(TeamMember.team_id == team.id).all()
