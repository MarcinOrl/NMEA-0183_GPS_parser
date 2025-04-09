import re
from collections import defaultdict


class GPSParser:
    def __init__(self):
        self.position = {}
        self.visible_sats = []
        self.used_sats = []

    def parse_line(self, line: str):
        line = line.strip()
        if not line.startswith("$") or "*" not in line:
            print(f"{line} -> odrzucona")
            return

        prefix = line[1:6]
        if not prefix.startswith("GP") or prefix[2:] not in {
            "RMC",
            "GGA",
            "GSA",
            "GSV",
            "GLL",
        }:
            print(f"{line} -> odrzucona")
            return

        print(f"{line} -> zaakceptowana")
        fields = line.split(",")

        # Parsowanie wg typu
        if prefix == "GPRMC":
            self._parse_gprmc(fields)
        elif prefix == "GPGGA":
            self._parse_gpgga(fields)
        elif prefix == "GPGSA":
            self._parse_gpgsa(fields)
        elif prefix == "GPGSV":
            self._parse_gpgsv(fields)
        elif prefix == "GPGLL":
            self._parse_gpgll(fields)

        self._print_state()

    def _parse_gprmc(self, f):
        self.position.update(
            {
                "czas": f[1],
                "szerokość": self._parse_coord(f[3], f[4]),
                "długość": self._parse_coord(f[5], f[6]),
                "prędkość": f[7],
                "kurs": f[8],
                "data": f[9],
                "odch.mag.": f[10] + f[11] if f[10] and f[11] else None,
            }
        )

    def _parse_gpgga(self, f):
        self.position.update(
            {"wysokość": f[9], "ilość sat.": f[7], "jakość": f[6], "geoid": f[11]}
        )

    def _parse_gpgsa(self, f):
        self.used_sats = [s for s in f[3:15] if s]
        self.position.update(
            {
                "tryb": f[2],
                "PDOP": f[15],
                "HDOP": f[16],
                "VDOP": f[17].split("*")[0] if f[17] else None,
            }
        )

    def _parse_gpgsv(self, f):
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
                "czas": f[5],
                "szerokość": self._parse_coord(f[1], f[2]),
                "długość": self._parse_coord(f[3], f[4]),
            }
        )

    def _parse_coord(self, val, dir):
        if not val:
            return None
        deg = float(val[:2]) if dir in ("N", "S") else float(val[:3])
        min = float(val[2:]) if dir in ("N", "S") else float(val[3:])
        dec = deg + min / 60
        return f"{dec:.6f} {dir}"

    def _print_state(self):
        print("\n[POZYCJA]")
        for k in [
            "czas",
            "data",
            "szerokość",
            "długość",
            "wysokość",
            "prędkość",
            "kurs",
        ]:
            if k in self.position:
                print(f"{k.capitalize():<12}: {self.position[k]}")
        print("\n[UŻYTE SATELITY]")
        print(", ".join(self.used_sats) if self.used_sats else "Brak")
        print("\n[WIDOCZNE SATELITY]")
        for s in self.visible_sats:
            print(
                f"ID: {s['id']}, Elev: {s['elev']}, Azymut: {s['azymut']}, SNR: {s['snr']}"
            )
        print("-" * 40)


def main():
    parser = GPSParser()
    with open("gps_data.txt", "r") as file:
        for line in file:
            parser.parse_line(line)


if __name__ == "__main__":
    main()
