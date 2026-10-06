from typing import Optional
from pimfp.model import AppUser, AppRole, AppUserRole


def exists_email(email: str) -> bool:
    """
    SELECT EXISTS(
        SELECT 1
        FROM `app_user`
        WHERE `email`=${email}
    );
    """
    return AppUser.select().where(AppUser.email == email).exists()


def get_user_by_email(email: str) -> Optional[AppUser]:
    """
    SELECT `id`, `email`, `organization`, `password`, `status`, `created_at`, `updated_at`
    FROM `app_user`
    WHERE `email`=${email}
    """
    return AppUser.get_or_none(AppUser.email == email)


def create_user(email: str, password: str, organization: str) -> AppUser:
    """
    INSERT INTO `app_user` (`email`, `password`, `organization`)
    VALUES (${email}, ${password}, ${organization})
    """
    user = AppUser.create(
        email=email,
        password=password,
        organization=organization
    )
    return user


def query_user_roles_by_email(email: str) -> list[AppRole]:
    """
    SELECT *
    FROM `app_role`
    INNER JOIN `app_user_role` ON `app_role`.`id` = `app_user_role`.`role_id`
    WHERE `app_user_role`.`email` = ${email}
    """
    return list(
        AppRole.select()
        .join(AppUserRole, on=(AppRole.id == AppUserRole.role_id))
        .where(AppUserRole.email == email)
    )


def has_role(email: str, role_code: str) -> bool:
    """
    SELECT EXISTS(
        SELECT 1 FROM `app_role`
        INNER JOIN `app_user_role` ON `app_role`.`id` = `app_user_role`.`role_id`
        WHERE `app_user_role`.`email` = ${email} AND `app_role`.`code` = ${role_code}
    )
    """
    return (
        AppRole.select()
        .join(AppUserRole, on=(AppRole.id == AppUserRole.role_id))
        .where(
            (AppUserRole.email == email) &
            (AppRole.code == role_code)
        )
        .exists()
    )


def update_user_password(email: str, password: str) -> bool:
    """
    UPDATE `app_user`
    SET `password`=${password}
    WHERE `email`=${email}
    """
    rows = AppUser.update(password=password).where(AppUser.email == email).execute()
    return rows > 0


def update_organization(email: str, organization: str) -> bool:
    """
    UPDATE `app_user`
    SET `organization`=${organization}
    WHERE `email`=${email}
    """
    rows = AppUser.update(organization=organization).where(AppUser.email == email).execute()
    return rows > 0
