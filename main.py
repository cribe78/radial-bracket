#!/usr/bin/env python3
# This is a sample Python script.
import argparse
import math
import unittest
from PIL import Image, ImageDraw, ImageShow, ImageFont
from typing import Dict
import os
import json


class Team:
    def __init__(self, background_color: tuple, logo: str):
        self.background_color = background_color
        self.bg = background_color
        search_paths = [os.path.join("logos", logo), logo]
        logo_path = None
        for sp in search_paths:
            if os.path.isfile(sp):
                logo_path = sp
                continue
        if logo_path:
            self.logo = Image.open(logo_path).convert("RGBA")
        else:
            raise ValueError(f"no logo found for {logo}")


def load_teams():
    with open("teams.json") as file:
        team_list = json.load(file)
    teams = {}
    for t in team_list:
        t['color'].append(255)
        alpha_color = tuple(t['color'])
        teams[t['name']] = Team(alpha_color, t['logo'])
    return teams


class Match:
    def __init__(self, team1: Team, team2: Team, score: tuple = None, penalties: tuple = None):
        self.team1 = team1
        self.team2 = team2
        self.score = score
        self.penalties = penalties

    def winner(self):
        if self.score is None:
            return None
        elif self.score[0] > self.score[1]:
            return self.team1
        elif self.score[1] > self.score[0]:
            return self.team2
        elif self.penalties is None:
            return None
        elif self.penalties[0] > self.penalties[1]:
            return self.team1
        elif self.penalties[1] > self.penalties[0]:
            return self.team2


def load_matches(tournament, teams):
    t_files = [os.path.join("tournaments", f"{tournament}.json"), os.path.join("tournaments", tournament),
               f"{tournament}.json", tournament]

    t_path = None
    for t in t_files:
        if os.path.isfile(t):
            t_path = t
            continue

    with open(t_path) as file:
        match_list = json.load(file)

    matches = {}
    for m in match_list:
        pens = tuple(m['penalties']) if 'penalties' in m else None
        for i in ('team1', 'team2'):
            if m[i] not in teams:
                raise ValueError(f"Team {m[i]} is not defined")
        matches[m['number']] = Match(teams[m['team1']], teams[m['team2']], tuple(m['score']), pens)

    return matches


def round_of_match(match_num):
    if match_num == 0:
        return 0
    return math.floor(math.log2(match_num)) + 1


class Bracket:
    def __init__(self, *, teams: Dict, matches: Dict, background=None, round_radius=120, line_width1=16,
                 font="fonts/Roboto/Roboto-Bold.ttf"):
        self.teams = teams
        self.matches = matches
        self.max_match = max(self.matches.keys())
        self.rounds = math.floor(math.log2(self.max_match)) + 2
        self.rr = round_radius

        if background:
            self.base = Image.open(background).convert("RGBA")
        else:
            im_dim = self.rr * 2 * (self.rounds + 1)
            self.base = Image.new("RGBA", (im_dim, im_dim))

        self.origin = (math.floor(self.base.size[0]/2), math.floor(self.base.size[1]/2))
        self.no_team_color1 = (160, 160, 160, 255)
        self.no_team_color2 = (200, 200, 200, 255)
        self.line_color = (255, 255, 255, 255)
        self.line_width1 = line_width1
        self.line_width2 = 2
        self.font = ImageFont.truetype(font, 38)
        self.font2 = ImageFont.truetype(font, 20)

    def create_image(self):
        for i in range(1, self.max_match + 1):
            im, mask = self.draw_match(i)
            self.base = Image.composite(im, self.base, mask)

        self.draw_match_0()
        return self.base

    def draw_match(self, match_num):
        mi = Image.new("RGBA", self.base.size)
        mask = Image.new("1", self.base.size)

        if not self.match_exists(match_num):
            return mi, mask

        d = ImageDraw.Draw(mi)
        md = ImageDraw.Draw(mask)

        mb = self.match_box(match_num)
        ma = self.match_angles(match_num)
        inside_box = self.match_box(math.floor(match_num/2))

        colors = self.match_colors(match_num)

        d.pieslice(mb, ma[0], ma[1], fill=colors[0], outline=self.line_color, width=self.line_width2)
        d.pieslice(mb, ma[1], ma[2], fill=colors[1], outline=self.line_color, width=self.line_width2)
        d.pieslice(mb, ma[0], ma[2], outline=self.line_color, width=self.line_width1)
        d.arc(mb, ma[0], ma[2], fill=self.line_color, width=self.line_width1)
        d.arc(inside_box, ma[0], ma[2], fill=self.line_color, width=self.line_width1)
        md.pieslice(mb, ma[0], ma[2], fill=1, outline=1, width=self.line_width1)
        md.pieslice(inside_box, ma[0], ma[2], fill=0)

        # Add logo
        logos = self.match_logos(match_num)
        logo_points = self.logo_centers(match_num)
        for i, logo in enumerate(logos):
            if logo:
                lp = (int(logo_points[i][0] - logo.size[0]/2), int(logo_points[i][1] - logo.size[1]/2))
                mi.alpha_composite(logo, dest=lp)

        # Add score
        if match_num in self.matches:
            match = self.matches[match_num]
            font_point, font_rotation, reverse = self.font_point(match_num)
            f_im = Image.new("RGBA", (100, 100))
            f_draw = ImageDraw.Draw(f_im)
            f_draw.text((50, 50), "-", fill=self.line_color, font=self.font, anchor="mm")

            if reverse:
                s2, s1 = match.score
                if match.penalties:
                    p2, p1 = match.penalties
            else:
                s1, s2 = match.score
                if match.penalties:
                    p1, p2 = match.penalties

            if match.penalties:
                f_draw.text((48, 50), f"{s1} ", fill=self.line_color, font=self.font, anchor="rb")
                f_draw.text((52, 50), f" {s2}", fill=self.line_color, font=self.font, anchor="lb")
                f_draw.text((48, 54), f"({p1})  ", fill=self.line_color, font=self.font2, anchor="rt")
                f_draw.text((52, 54), f"  ({p2})", fill=self.line_color, font=self.font2, anchor="lt")

            elif match.score:
                f_draw.text((50, 50), f"{s1} ", fill=self.line_color, font=self.font, anchor="rm")
                f_draw.text((50, 50), f" {s2}", fill=self.line_color, font=self.font, anchor="lm")

            comp_point = (font_point[0] - 50, font_point[1] - 50)
            f_rot = f_im.rotate(font_rotation, center=(50, 50))
            mi.alpha_composite(f_rot, dest=comp_point)

        return mi, mask

    def draw_match_0(self):
        d = ImageDraw.Draw(self.base)
        fill = None
        logo = None
        if 1 in self.matches:
            winner = self.matches[1].winner()
            if winner:
                fill = winner.bg
                logo = winner.logo

        d.pieslice(self.match_box(0), 0, 360, fill=fill, outline=self.line_color, width=self.line_width1)

        if logo:
            offset = (-1 * logo.size[0] + self.origin[0], -1 * logo.size[1] + self.origin[1])
            big_logo = logo.resize((logo.size[0] * 2, logo.size[1] * 2), Image.Resampling.BICUBIC)
            self.base.alpha_composite(big_logo, offset)

    def feeder_matches(self, match_num):
        f_nums = (match_num * 2, match_num * 2 + 1)
        f1 = self.matches[f_nums[0]] if f_nums[0] in self.matches else None
        f2 = self.matches[f_nums[1]] if f_nums[1] in self.matches else None
        return f1, f2

    def font_point(self, match_num):
        _, a, _ = self.match_angles(match_num)
        a_rad = math.radians(a)
        round_num = round_of_match(match_num)
        dist = self.rr * (round_num + .5) - self.line_width1 / 2
        ox, oy = self.origin
        p = (int(ox + dist * math.cos(a_rad)), int(oy + dist * math.sin(a_rad)))

        reverse = False
        rot = 270 - a
        if 270 > rot > 90:
            reverse = True
            rot = rot - 180
        return p, rot, reverse

    def match_exists(self, match_num):
        if match_num in self.matches:
            return True
        if match_num > self.max_match:
            return False

        return self.match_exists(match_num * 2) or self.match_exists(match_num * 2 + 1)

    def logo_centers(self, match_num):
        a0, a1, a2 = self.match_angles(match_num)
        a_l1 = math.radians((a0 + a1)/2)
        a_l2 = math.radians((a1 + a2)/2)

        round_num = round_of_match(match_num)
        l_dist = self.rr * (round_num + .5) - self.line_width1 / 2

        ox, oy = self.origin
        p1 = (ox + l_dist * math.cos(a_l1), oy + l_dist * math.sin(a_l1))
        p2 = (ox + l_dist * math.cos(a_l2), oy + l_dist * math.sin(a_l2))

        return p1, p2

    def match_box(self, match_num):
        ox, oy = self.origin
        round_num = round_of_match(match_num)
        br = self.rr * (round_num + 1)

        return [(ox - br, oy - br), (ox + br, oy + br)]

    def match_colors(self, match_num):
        colors = [self.no_team_color1, self.no_team_color2]
        teams = self.match_teams(match_num)
        for i in (0, 1):
            if teams[i]:
                colors[i] = teams[i].bg
        return colors

    def match_angles(self, match_num):
        r_num = round_of_match(match_num)
        r_teams = 2 ** r_num
        r_games = r_teams / 2

        game_arc = 360 * 1 / r_games
        team_arc = 360 * 1 / r_teams

        game_offset = -90 + 360 * (match_num - r_games) / r_games

        return game_offset, game_offset + team_arc, game_offset + game_arc

    def match_logos(self, match_num):
        logos = [None, None]
        teams = self.match_teams(match_num)
        for i in (0, 1):
            if teams[i]:
                logos[i] = teams[i].logo
        return logos

    def match_teams(self, match_num):
        teams = [None, None]
        if match_num in self.matches:
            match = self.matches[match_num]
            teams = [match.team1, match.team2]
        else:
            feeders = self.feeder_matches(match_num)
            for i in (0,1):
                if feeders[i] and feeders[i].winner():
                    teams[i] = feeders[i].winner()
        return teams


def create_bracket_image(tournament, outfile=None):
    teams = load_teams()
    matches = load_matches(tournament, teams)
    bracket = Bracket(teams=teams, matches=matches)
    im_out = bracket.create_image()

    if outfile:
        im_out.save(outfile)
    else:
        ImageShow.show(im_out)


t = {
    'SEA': Team((94, 153, 65, 255), "logos/sounders.png"),
    'PUM': Team((146, 133, 84, 255), "logos/pumas.png"),
    'MTG': Team((13, 66, 110, 255), "logos/motagua.png"),
    'SAP': Team((139, 24, 73, 255), "logos/saprissa.png"),
    'NER': Team((14, 34, 64, 255), "logos/revs.png")
}



class TestBracket(unittest.TestCase):

    def setUp(self):
        self.SEA_COLOR = (94, 153, 65, 255)
        self.PUM_COLOR = (146, 133, 84, 255)
        self.test_teams = {
            'SEA': Team(self.SEA_COLOR, "logos/sounders.png"),
            'PUM': Team(self.PUM_COLOR, "logos/pumas.png"),
            'MTG': Team((13, 66, 110, 255), "logos/motagua.png"),
            'SAP': Team((139, 24, 73, 255), "logos/saprissa.png"),
            'NER': Team((14, 34, 64, 255), "logos/revs.png")
        }

        self.test_matches = {
            1: Match(t['PUM'], t['SEA'], (1, 3)),
            4: Match(t['PUM'], t['NER'], (3, 3), (4, 3)),
            8: Match(t['PUM'], t['SAP'], (6, 3)),
            14: Match(t['MTG'], t['SEA'], (0, 5))
        }

        self.bracket = Bracket(teams=self.test_teams, matches=self.test_matches)

    def test_default_size(self):
        self.assertEqual(5, self.bracket.rounds)
        self.assertEqual((600, 600), self.bracket.origin)
        self.assertEqual((1200, 1200), self.bracket.base.size)

    def test_box(self):
        self.assertEqual([(400, 400), (800, 800)], self.bracket.match_box(1))
        self.assertEqual([(300, 300), (900, 900)], self.bracket.match_box(3))
        self.assertEqual([(100, 100), (1100, 1100)], self.bracket.match_box(11))

    def test_angles(self):
        self.assertEqual((-90, -45, 0), self.bracket.match_angles(4))
        self.assertEqual((90, 112.5, 135), self.bracket.match_angles(12))

    def test_match_colors(self):
        self.assertEqual([self.PUM_COLOR, self.SEA_COLOR], self.bracket.match_colors(1))
        self.assertEqual([self.SEA_COLOR, self.bracket.no_team_color2], self.bracket.match_colors(7))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a radial bracket image')
    parser.add_argument('--tournament', '-t', help='The name of the tournament file to load', default="ccl2022")
    parser.add_argument('--outfile', '-o', help="Output file path", default=None)
    args = parser.parse_args()

    create_bracket_image(args.tournament, args.outfile)



