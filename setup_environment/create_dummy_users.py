from sqlalchemy import text

from app_common.common.talent_config_manager import load_gettalent_config
from app_common.common.talent_flask import TalentFlask
from common.models.db import db


def create_dummy_users():
    app = TalentFlask(__name__)
    load_gettalent_config(app.config)
    db.init_app(app)
    db.app = app
    db.reflect()
    """
    Create three dummy users in db
    :return:
    """
    # Assigned `Talent_Admin` (3) role to test users that will be used to run api based tests.
    q = '''INSERT INTO domain (name,organizationId, is_disabled) VALUES ("test_domain_first",1, 0);
    INSERT INTO domain (name,organizationId, is_disabled) VALUES ("test_domain_second",1,0);
    INSERT INTO user_group (name, DomainId) VALUES ("test_group_first", 1), ("test_group_second", 2);
    INSERT INTO user (email, password, domainId, userGroupId, is_disabled, roleId)
    VALUES ("test_email@test.com", "pbkdf2:sha512:1000$lf3teYeJ$7bb470eb0a2d10629e4835cac771e51d2b1e9ed577b849c27551ab7b244274a10109c8d7a7b8786f4de176b764d9763e4fd1954ad902d6041f6d46fab16219c6", 1, 1, 0, 3);
    INSERT INTO user (email, password, domainId, userGroupId, is_disabled, roleId)
    VALUES ("test_email_same_domain@test.com", "pbkdf2:sha512:1000$lf3teYeJ$7bb470eb0a2d10629e4835cac771e51d2b1e9ed577b849c27551ab7b244274a10109c8d7a7b8786f4de176b764d9763e4fd1954ad902d6041f6d46fab16219c6", 1, 1, 0, 3);
    INSERT INTO user (email, password, domainId, userGroupId, is_disabled, roleId)
    VALUES ("test_email_second@test.com", "pbkdf2:sha512:1000$lf3teYeJ$7bb470eb0a2d10629e4835cac771e51d2b1e9ed577b849c27551ab7b244274a10109c8d7a7b8786f4de176b764d9763e4fd1954ad902d6041f6d46fab16219c6", 2, 2, 0, 3);
    INSERT INTO client (client_id, client_secret, client_name)
    VALUES ("KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921U1Z", "DbS8yb895bBw4AXFe182bjYmv5XfF1x7dOftmBHMlxQmulYj1Z", "test_client");
    INSERT INTO token VALUES (1,'KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921U1Z',1,'Bearer','uTl6zNUdoNATwwUg0GOuSFvyrtyCCW','N1tLeTlP7LZUt3QILZyQw957s38AKB','2017-03-11 08:44:18',''),
    (2,'KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921U1Z',2,'Bearer','9ery8pVOxTOvQU0oJsENRek4lj6ZT6','oRojE4Gu4KY29TXO11yh1AcZLGjOhM','2017-03-25 12:29:49',''),
    (3,'KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921U1Z',3,'Bearer','iM0WU5y76laIJph5LS1jidKcdjWk4a','JdRrBdcm9N7cfhjjcUUIRWGU7UVBuy','2017-03-27 00:40:30','');
    '''

    sql = text(q)
    result = db.engine.execute(sql)
