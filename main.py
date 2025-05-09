class GPSParser:
    def __init__(self):
        self.position = {}
        self.visible_sats = []
        self.used_sats = []
        self.log = open("parser_output.log", "w", encoding="utf-8")

    def _format_time(self, t):
        if not t or len(t) < 6:
            return "-"
        h, m, s = int(t[:2]), int(t[2:4]), int(t[4:6])
        return f"{h}:{m:02}:{s:02}"

    def _format_date(self, d):
        if not d or len(d) < 6:
            return "-"
        day = int(d[:2])
        month = int(d[2:4])
        year = 2000 + int(d[4:6])
        return f"{day}.{month}.{year}"

    def _format_mag_var(self, value, direction):
        if not value or not direction:
            return "-"
        return f"{float(value):.1f}º {direction}"

    def _format_coord_dms(self, val, dir):
        if not val:
            return "-"
        degrees = int(val[:2]) if dir in ("N", "S") else int(val[:3])
        minutes = float(val[2:]) if dir in ("N", "S") else float(val[3:])
        return f"{degrees}º{minutes:.4f}’ {dir}"

    def _format_angle(self, val):
        try:
            angle = float(val)
            return f"{angle:.1f}º"
        except:
            return "-"

    def _format_mode(self, mode_sel, fix_type):
        mode_map = {"A": "automatyczny", "M": "manualny"}
        fix_map = {"1": "brak", "2": "2D", "3": "3D"}
        return f"{mode_map.get(mode_sel, '-')}, {fix_map.get(fix_type, '-')}"

    def _clean_float(self, val):
        try:
            return (
                str(float(val)).rstrip("0").rstrip(".") if "." in val else str(int(val))
            )
        except:
            return val

    def parse_line(self, line: str):
        line = line.strip()
        if not line.startswith("$") or "*" not in line:
            print(f"{line} -> odrzucona", file=self.log)
            return

        system = line[1:3]
        sentence = line[3:6]

        if system not in {"GP", "GL", "GB"} or sentence not in {
            "RMC",
            "GGA",
            "GSA",
            "GSV",
            "GLL",
        }:
            print(f"{line} -> odrzucona", file=self.log)
            return

        print(f"{line} -> zaakceptowana", file=self.log)

        if "*" in line:
            checksum = line.split("*")[-1]
            self.position["suma_kontrolna"] = checksum

        fields = line.split(",")

        if sentence == "RMC":
            self._parse_gprmc(fields)
        elif sentence == "GGA":
            self._parse_gpgga(fields)
        elif sentence == "GSA":
            self._parse_gpgsa(fields)
        elif sentence == "GSV":
            self._parse_gpgsv(fields)
        elif sentence == "GLL":
            self._parse_gpgll(fields)

        self._print_state()

    def _parse_gprmc(self, f):
        mag_val = f[10]
        direction = f[11][0] if f[11] else "-"
        self.position.update(
            {
                "czas": self._format_time(f[1]),
                "szerokość": self._format_coord_dms(f[3], f[4]),
                "długość": self._format_coord_dms(f[5], f[6]),
                "prędkość": self._clean_float(f[7]),
                "kurs": self._format_angle(f[8]),
                "data": self._format_date(f[9]),
                "odch.mag.": self._format_mag_var(mag_val, direction),
                "status": "aktywny" if f[2] == "A" else "nieaktywny",
            }
        )

    def _parse_gpgga(self, f):
        self.position.update(
            {
                "wysokość": f[9],
                "ilość sat.": f[7],
                "jakość": f[6],
                "geoid": f[11],
                "HDOP": f[8],
            }
        )

    def _parse_gpgsa(self, f):
        self.used_sats = [s for s in f[3:15] if s]
        self.position.update(
            {
                "tryb": self._format_mode(f[1], f[2]),
                "PDOP": f[15],
                "HDOP": f[16],
                "VDOP": f[17].split("*")[0] if f[17] else None,
            }
        )

    def _parse_gpgsv(self, f):
        try:
            total_msgs = int(f[1])
            msg_num = int(f[2])
            total_sats = int(f[3])
        except:
            return

        if msg_num == 1:
            self.visible_sats = []
            self.position["total_sats"] = str(total_sats)

        for i in range(4, len(f) - 1, 4):
            try:
                sat = {
                    "id": f[i],
                    "elev": f[i + 1],
                    "azymut": f[i + 2],
                    "snr": f[i + 3].split("*")[0],
                }
                self.visible_sats.append(sat)
            except IndexError:
                break

    def _parse_gpgll(self, f):
        self.position.update(
            {
                "czas": self._format_time(f[5]),
                "szerokość": self._format_coord_dms(f[1], f[2]),
                "długość": self._format_coord_dms(f[3], f[4]),
                "status": "aktywny" if len(f) > 6 and f[6] == "A" else "nieaktywny",
            }
        )

    def _print_state(self):
        log = self.log

        print("\nINFORMACJE SYSTEMOWE:", file=log)
        print(
            f"{'Data':<18}"
            f"{'Czas':<18}"
            f"{'Odch.mag.':<15}"
            f"{'Wys.geoid':<12}"
            f"{'Tryb':<22}"
            f"{'Jakość':<10}"
            f"{'Suma kontrolna':<18}",
            file=log,
        )
        print(
            f"{self.position.get('data', '-'):18}"
            f"{self.position.get('czas', '-'):18}"
            f"{self.position.get('odch.mag.', '-'):15}"
            f"{self.position.get('geoid', '-'):12}"
            f"{self.position.get('tryb', '-'):22}"
            f"{self.position.get('jakość', '-'):10}"
            f"{self.position.get('suma_kontrolna', '-'):18}",
            file=log,
        )

        print("\nPOZYCJA URZĄDZENIA:", file=log)
        print(
            f"{'Szer.geogr.':<18}"
            f"{'Dł.geogr.':<18}"
            f"{'Prędkość':<12}"
            f"{'Kąt ruchu':<12}"
            f"{'Wysokość':<12}"
            f"{'HDOP':<10}"
            f"{'VDOP':<10}"
            f"{'PDOP':<10}"
            f"{'Liczba sat.':<15}"
            f"{'ID satelitów':<30}"
            f"{'Status':<10}",
            file=log,
        )
        print(
            f"{self.position.get('szerokość', '-'):18}"
            f"{self.position.get('długość', '-'):18}"
            f"{self.position.get('prędkość', '-'):12}"
            f"{self.position.get('kurs', '-'):12}"
            f"{self.position.get('wysokość', '-'):12}"
            f"{self.position.get('HDOP', '-'):10}"
            f"{self.position.get('VDOP', '-'):10}"
            f"{self.position.get('PDOP', '-'):10}"
            f"{self.position.get('ilość sat.', '-'):15}"
            f"{', '.join(self.used_sats) if self.used_sats else '-':30}"
            f"{self.position.get('status', '-'):10}",
            file=log,
        )

        print("\nDANE O SATELITACH:", file=log)
        print(
            f"{'Czas pozycji':<18}"
            f"{'Liczba widocznych':<22}"
            f"{'ID':<6}"
            f"{'Elev.':<8}"
            f"{'Azymut':<8}"
            f"{'SNR':<6}",
            file=log,
        )

        if self.visible_sats:
            for sat in self.visible_sats:
                print(
                    f"{self.position.get('czas', '-'):18}"
                    f"{self.position.get('total_sats', '-'):22}"
                    f"{sat['id']:<6}"
                    f"{sat['elev']:<8}"
                    f"{sat['azymut']:<8}"
                    f"{sat['snr']:<6}",
                    file=log,
                )
        else:
            print("-" * 80, file=log)

        print("=" * 150, file=log)


def main():
    parser = GPSParser()
    with open("gps_data.txt", "r") as file:
        for line in file:
            parser.parse_line(line)
    parser.log.close()
    print("Dane zapisane do parser_output.log")


if __name__ == "__main__":
    main()
