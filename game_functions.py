import sys
from time import sleep
import pygame
from bullet import Bullet
from alien import Alien

'''存储大量让游戏运行的函数'''

def check_keydown_events(event, ai_settings, screen, stats, ship, bullets):
    """响应按键"""
    if event.key == pygame.K_RIGHT:
        # 向右移动飞船
        ship.moving_right = True
    elif event.key == pygame.K_LEFT:
        # 向左移动飞船
        ship.moving_left = True
    elif event.key == pygame.K_SPACE:
        fire_bullet(ai_settings, screen, ship, bullets)
    elif event.key == pygame.K_q:
        # 按Q来结束游戏
        save_high_score(stats)
        sys.exit()

def check_keyup_events(event, ship):
    """响应松开"""
    if event.key == pygame.K_RIGHT:
        ship.moving_right = False
    elif event.key == pygame.K_LEFT:
        ship.moving_left = False

def check_events(ai_settings, screen, stats, sb, play_button, ship, aliens, bullets):
    '''响应按键和鼠标事件'''
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_high_score(stats)
            sys.exit()

        elif event.type == pygame.KEYDOWN:      #每次按键都被注册为一个KEYDOWN事件
            check_keydown_events(event, ai_settings, screen, stats, ship, bullets)

        elif event.type == pygame.KEYUP:    #每次松开都被注册为一个KEYUP事件
            check_keyup_events(event, ship)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()   # pygame.mouse.get_pos()返回一个元组，其中包含玩家单击时鼠标的x和y坐标
            check_play_button(ai_settings, screen, stats, sb, play_button, ship, aliens, bullets, mouse_x, mouse_y)

def check_play_button(ai_settings, screen, stats, sb, play_button, ship, aliens, bullets, mouse_x, mouse_y):
    """在玩家单击开始按钮时开始新游戏"""
    button_clicked = play_button.rect.collidepoint(mouse_x, mouse_y)    # collidepoint()检查鼠标单击位置是否在开始按钮的rect内
    if button_clicked and not stats.game_active:    # 仅当玩家单击了开始按钮且游戏当前处于非活动状态时，游戏才重新开始
                                                    # 目的是避免出现游戏过程中单击开始按钮区域游戏依然做出响应
        # 重置游戏设置
        ai_settings.initialize_dynamic_settings()

        # 隐藏光标
        pygame.mouse.set_visible(False)

        # 重置游戏统计信息
        stats.reset_stats()
        stats.game_active = True

        # 重置记分牌图像
        sb.prep_score()
        sb.prep_high_score()
        sb.prep_level()
        sb.prep_ships()

        # 清空外星人列表和子弹列表
        aliens.empty()
        bullets.empty()

        # 创建一群新的外星人，并让飞船居中
        create_fleet(ai_settings, screen, ship, aliens)
        ship.center_ship()

def update_screen(ai_settings, screen, stats, sb, ship, aliens, bullets, play_button):
    '''更新屏幕上的图像，并切换到新屏幕'''
    # 每次循环都重绘屏幕
    screen.fill(ai_settings.bg_color)
    # 在飞船和外星人后面重绘所有子弹
    for bullet in bullets.sprites():    # 方法bullets.sprites()返回一个列表，其中包含编组bullets中的所有精灵
        bullet.draw_bullet()

    ship.blitme()
    aliens.draw(screen)

    # 显示得分
    sb.show_score()

    # 如果游戏处于非活动状态，就绘制“开始”按钮
    if not stats.game_active:
        play_button.draw_button()

    # 让最近绘制的屏幕可见
    pygame.display.flip()

def update_bullets(ai_settings, screen, stats, sb, ship, aliens, bullets):
    """更新子弹的位置，并删除已消失的子弹"""
    # 更新子弹的位置
    bullets.update()

    # 删除已消失的子弹
    for bullet in bullets.copy():
        if bullet.rect.bottom <= 0:
            bullets.remove(bullet)
    # print(len(bullets))
    check_bullet_alien_collisions(ai_settings, screen, stats, sb, ship, aliens, bullets)

def check_bullet_alien_collisions(ai_settings, screen, stats, sb, ship, aliens, bullets):
    """响应子弹和外星人的碰撞"""
    # 删除发生碰撞的子弹和外星人
    # 子弹击中外星人后我们要马上知道，以便发生碰撞后让外星人消失，所以在更新子弹的位置后立即检测碰撞
    # 检查是否有子弹击中了外星人。如果是这样，就删除相应的子弹和外星人
    collisions = pygame.sprite.groupcollide(bullets, aliens, True, True)
    '''
    方法sprite.groupcollide()将每颗子弹的rect同每个外星人的rect进行比较，并返回一个字典，其中包含了发生碰撞的子弹和外星人。
    这行代码先遍历编组bullets中的每颗子弹，再遍历编组aliens中的每个外星人。
    每当有子弹和外星人的rect重叠时，就在此方法返回的字典中添加一个键值对。
    两个实参True告诉Pygame删除发生碰撞的子弹和外星人
    '''
    if collisions:
        for alien in collisions.values():   # collisions中每个值都是一个列表，包含被同一颗子弹击中的所有外星人
            stats.score += ai_settings.alien_points * len(collisions.values())
            sb.prep_score()
        check_high_score(stats, sb)

    if len(aliens) == 0:  # 检测外星人编组是否为空
        # 删除现有的子弹并、加快游戏节奏，并新建一群外星人
        # 如果整群外星人被消灭，就提高一个等级
        bullets.empty()
        ai_settings.increase_speed()

        # 提高等级
        stats.level += 1
        sb.prep_level()

        create_fleet(ai_settings, screen, ship, aliens)


def fire_bullet(ai_settings, screen, ship, bullets):
    """如果还没有到达限制，就发射一颗子弹"""
    # 创建一颗子弹并将其加入到编组bullets中
    if len(bullets) < ai_settings.bullets_allowed:
        new_bullet = Bullet(ai_settings, screen, ship)
        bullets.add(new_bullet)

def create_fleet(ai_settings, screen, ship, aliens):
    """创建外星人群"""
    # 创建一个外星人，并计算一行可容纳多少个外星人
    # 外星人间距为外星人宽度
    alien = Alien(ai_settings, screen)
    number_aliens_x = get_number_aliens_x(ai_settings, alien.rect.width)    # 每行可容纳的外星人个数
    number_row = get_number_rows(ai_settings, ship.rect.height, alien.rect.height)  # 外星人行数

    # 创建外星人群
    for row_number in range(number_row):
        for alien_number in range(number_aliens_x):
            create_alien(ai_settings, screen, aliens, alien_number, row_number)


def get_number_aliens_x(ai_settings, alien_width):
    """计算每行可容纳多少外星人"""
    available_space_x = ai_settings.screen_width - 2 * alien_width  # 在屏幕两端留下一定边距，设置为外星人宽度
    number_aliens_x = int(available_space_x / (2 * alien_width))  # 一行可容纳的外星人数量
    return number_aliens_x

def create_alien(ai_settings, screen, aliens, alien_number, row_number):
    """创建一个外星人并将其放在当前行"""
    # 创建一个外星人并加入当前行
    alien = Alien(ai_settings, screen)
    alien_width = alien.rect.width
    alien.x = alien_width + 2 * alien_width * alien_number
    alien.rect.x = alien.x
    alien.rect.y = 2 * alien.rect.height + 2 * alien.rect.height * row_number
    aliens.add(alien)

def get_number_rows(ai_settins, ship_height, alien_height):
    """计算屏幕可容纳多少行外星人"""
    available_space_y = (ai_settins.screen_height -
                         (3 * alien_height) - ship_height)  # 可用垂直空间：将屏幕高度减去第一行外星人的上边距（外星人高度）、飞船高度
                                                            # 以及最初外星人高度加上外星人间距（外星人高度两倍）
    number_rows = int(available_space_y / (2 * alien_height))   # 可容纳行数：将可用垂直空间除以外星人高度的两倍
    return number_rows

def check_fleet_edges(ai_settings, aliens):
    """有外星人到达边缘时采取相应的措施"""
    for alien in aliens.sprites():
        if alien.check_edges():
            change_fleet_direction(ai_settings, aliens)
            break

def change_fleet_direction(ai_settings, aliens):
    """将整群外星人下移，并改变它们的方向"""
    for alien in aliens.sprites():
        alien.rect.y += ai_settings.fleet_drop_speed
    ai_settings.fleet_direction *= -1

def ship_hit(ai_settings, screen, stats, sb, ship, aliens, bullets):
    """响应被外星人撞到的飞船"""
    if stats.ships_left > 0:
        # 将ship_left减1
        stats.ships_left -= 1

        # 更新记分牌
        sb.prep_ships()

        # 清空外星人列表和子弹列表
        aliens.empty()
        bullets.empty()

        # 创建一群新的外星人，并将飞船放到屏幕底端中央
        create_fleet(ai_settings, screen, ship, aliens)
        ship.center_ship()

        # 暂停
        sleep(1)
    else:
        stats.game_active = False
        pygame.mouse.set_visible(True)  # 游戏结束后显示光标

def check_aliens_bottom(ai_settings, screen, stats, sb, ship, aliens, bullets):
    """检查是否有外星人到达了屏幕底端"""
    screen_rect = screen.get_rect()
    for alien in aliens.sprites():
        if alien.rect.bottom >= screen_rect.bottom:
            # 像飞船被撞到一样进行处理
            ship_hit(ai_settings, screen, stats, sb, ship, aliens, bullets)
            break


def update_aliens(ai_settings, screen, stats, sb, ship, aliens, bullets):
    """检查是否有外星人位于屏幕边缘，并更新整群外星人的位置"""
    check_fleet_edges(ai_settings, aliens)
    aliens.update()
    # 检测外星人和飞船之间的碰撞
    if pygame.sprite.spritecollideany(ship, aliens):
        ship_hit(ai_settings, screen, stats, sb, ship, aliens, bullets)
    # 检查是否有外星人到达屏幕底端
    check_aliens_bottom(ai_settings, screen, stats, sb, ship, aliens, bullets)

def check_high_score(stats, sb):
    """检查是否诞生了新的最高得分"""
    if stats.score > stats.high_score:
        stats.high_score = stats.score
        sb.prep_high_score()

def save_high_score(stats):
    """将最高分存档"""
    filename = 'highscore.txt'
    with open(filename, 'r') as f_o:
        contents = f_o.read()
        # 当出现更高分数时才存档
    with open(filename, 'w') as f_o:
        if stats.score >= int(contents):
            f_o.write(str(stats.score))
        else:
            f_o.write(contents)     # 防止文件被直接清空


